"""
FastAPI backend tests using AAA (Arrange-Act-Assert) pattern.
"""
import copy
import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


# Store initial state for fixture
INITIAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test."""
    activities.clear()
    activities.update(copy.deepcopy(INITIAL_ACTIVITIES))
    yield


client = TestClient(app)


class TestGetActivities:
    """Test cases for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns all available activities."""
        # Arrange
        # (activities are loaded by the fixture)

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_includes_participant_count(self):
        """Test that activity data includes participants list."""
        # Arrange
        # (activities are loaded by the fixture)

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "participants" in data["Chess Club"]
        assert isinstance(data["Chess Club"]["participants"], list)


class TestSignupForActivity:
    """Test cases for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_participant_success(self):
        """Test successful signup of a new participant."""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert email in activities[activity]["participants"]
        assert response.json()["message"] == f"Signed up {email} for {activity}"

    def test_signup_duplicate_participant_fails(self):
        """Test that duplicate signup is rejected."""
        # Arrange
        activity = "Chess Club"
        existing_email = activities[activity]["participants"][0]

        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={existing_email}"
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_nonexistent_activity_fails(self):
        """Test that signup for nonexistent activity returns 404."""
        # Arrange
        email = "student@mergington.edu"
        nonexistent_activity = "FakeActivity"

        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_multiple_participants_different_activities(self):
        """Test that same participant can sign up for multiple activities."""
        # Arrange
        email = "versatile@mergington.edu"

        # Act
        response1 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        response2 = client.post(
            f"/activities/Programming%20Class/signup?email={email}"
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestRemoveParticipant:
    """Test cases for DELETE /activities/{activity_name}/participants endpoint."""

    def test_remove_existing_participant_success(self):
        """Test successful removal of a participant."""
        # Arrange
        activity = "Chess Club"
        email_to_remove = activities[activity]["participants"][0]

        # Act
        response = client.delete(
            f"/activities/{activity}/participants?email={email_to_remove}"
        )

        # Assert
        assert response.status_code == 200
        assert email_to_remove not in activities[activity]["participants"]
        assert response.json()["message"] == f"Removed {email_to_remove} from {activity}"

    def test_remove_nonexistent_participant_fails(self):
        """Test that removing a non-existent participant returns 404."""
        # Arrange
        activity = "Chess Club"
        nonexistent_email = "notregistered@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity}/participants?email={nonexistent_email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found"

    def test_remove_from_nonexistent_activity_fails(self):
        """Test that removing from nonexistent activity returns 404."""
        # Arrange
        nonexistent_activity = "FakeActivity"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{nonexistent_activity}/participants?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"


class TestActivityDataIntegrity:
    """Test cases for data consistency across operations."""

    def test_signup_and_get_reflects_new_participant(self):
        """Test that GET /activities reflects newly added participant."""
        # Arrange
        email = "tracker@mergington.edu"

        # Act
        client.post(f"/activities/Gym%20Class/signup?email={email}")
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert email in data["Gym Class"]["participants"]

    def test_remove_and_get_reflects_deletion(self):
        """Test that GET /activities reflects removed participant."""
        # Arrange
        activity = "Chess Club"
        email_to_remove = activities[activity]["participants"][0]

        # Act
        client.delete(f"/activities/{activity}/participants?email={email_to_remove}")
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert email_to_remove not in data[activity]["participants"]

    def test_signup_updates_availability_count(self):
        """Test that max_participants and spot count are tracked correctly."""
        # Arrange
        activity = "Chess Club"
        initial_response = client.get("/activities")
        initial_participants = len(
            initial_response.json()[activity]["participants"]
        )
        max_participants = initial_response.json()[activity]["max_participants"]

        # Act
        client.post(f"/activities/{activity}/signup?email=newperson@mergington.edu")

        # Assert
        response = client.get("/activities")
        updated_participants = len(
            response.json()[activity]["participants"]
        )
        assert updated_participants == initial_participants + 1
        assert updated_participants <= max_participants
