document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      // Clear and reset the activity select so options don't duplicate
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        // Build participants HTML (bulleted list)
        const participantsHtml = details.participants && details.participants.length
          ? `<div class="participants">
               <strong>Participants:</strong>
               <ul class="participants-list">
                 ${details.participants.map(p => `<li>${p}<span class=\"remove-participant\" data-activity=\"${name}\" data-email=\"${p}\">&times;</span></li>`).join('')}
               </ul>
             </div>`
          : `<div class="participants">
               <strong>Participants:</strong>
               <p class="no-participants">No participants yet.</p>
             </div>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          ${participantsHtml}
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        // refresh activities list so the new participant appears
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // delegate click events for participant removal
  activitiesList.addEventListener("click", async (event) => {
    if (event.target.classList.contains("remove-participant")) {
      const activity = event.target.dataset.activity;
      const email = event.target.dataset.email;
      try {
        const res = await fetch(
          `/activities/${encodeURIComponent(activity)}/participants?email=${encodeURIComponent(email)}`,
          { method: "DELETE" }
        );
        const data = await res.json();
        if (res.ok) {
          messageDiv.textContent = data.message;
          messageDiv.className = "info";
          messageDiv.classList.remove("hidden");
          setTimeout(() => messageDiv.classList.add("hidden"), 4000);
          fetchActivities();
        } else {
          messageDiv.textContent = data.detail || "Could not remove participant";
          messageDiv.className = "error";
          messageDiv.classList.remove("hidden");
        }
      } catch (err) {
        messageDiv.textContent = "Failed to remove participant";
        messageDiv.className = "error";
        messageDiv.classList.remove("hidden");
        console.error(err);
      }
    }
  });

  // Initialize app
  fetchActivities();
});
