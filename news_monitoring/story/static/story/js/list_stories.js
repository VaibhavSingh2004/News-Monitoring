
$(document).ready(function () {
    fetchStories(1);  // Load the first page on initial page load

    // Search and filter event
    $("#search-title, #filter-date").on("input change", function () {
        fetchStories(1);  // Reset to first page on new search
    });

    // Pagination event handlers (will be dynamically added later)
    $(document).on("click", ".pagination-link", function (e) {
        e.preventDefault();
        let page = $(this).data("page");  // Get the page number from button
        fetchStories(page);
    });
});

function fetchStories(page = 1) {
    $.ajax({
        url: storyListUrl,
        data: {
            q: $("#search-title").val().trim(),
            date: $("#filter-date").val(),
            page: page  // Pass the selected page number
        },
        dataType: "json",
        success: function (response) {
            let storiesList = $("#stories-list");
            storiesList.empty(); // Clear previous content

            if (!response.stories || response.stories.length === 0) {
                storiesList.append("<p>No results found.</p>");
                return;
            }
            console.log(response)

            response.stories.forEach(story => {
                let companies = story.tagged_companies.length
                    ? story.tagged_companies.join(", ")
                    : "No companies tagged";

                let persons = story.persons?.length
                    ? story.persons.join(", ")
                    : "None";

                let organizations = story.organizations?.length
                    ? story.organizations.join(", ")
                    : "None";

                let locations = story.locations?.length
                    ? story.locations.join(", ")
                    : "None";

                let viewDuplicatesBtn = story.has_duplicates
                    ? `<a href="/story/${story.id}/" class="btn duplicates-btn">View Duplicates</a>`
                    : "";


                storiesList.append(`
                    <div class="story-card">
                        <h3 class="story-title">
                            <a href="${story.article_url}" target="_blank">${story.title}</a>
                        </h3>
                        <p class="story-date"><strong>Published Date:</strong> ${story.published_date || "N/A"}</p>
                        <p class="story-body">${story.body_text}</p>

                        <p class="story-companies"><strong>Tagged Companies:</strong> ${companies}</p>
                        <p class="story-persons"><strong>Persons:</strong> ${persons}</p>
                        <p class="story-organizations"><strong>Organizations:</strong> ${organizations}</p>
                        <p class="story-locations"><strong>Locations:</strong> ${locations}</p>

                        <div class="story-actions">
                            <a href="/story/edit/${story.id}/" class="btn edit-btn">Edit</a>
                            <a href="/story/delete/${story.id}/" class="btn delete-btn" onclick="return confirm('Are you sure?');">Delete</a>
                            ${viewDuplicatesBtn}
                        </div>
                    </div>
                `);
            });

            // Update pagination controls
            updatePagination(response);
        },
        error: function (xhr) {
            console.error("AJAX Error:", xhr.responseText);
            alert("Failed to load stories. Please try again.");
        }
    });
}

// Update pagination buttons dynamically
