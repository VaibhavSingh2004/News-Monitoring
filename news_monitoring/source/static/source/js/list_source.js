$(document).ready(function () {
    fetchSources(1);

    // Re-fetch sources when search input changes
    $("#search-source").on("input", function () {
        fetchSources(1);
    });

    // Attach event handler for fetching stories
    $(document).on("click", ".fetch-story-btn", fetchStories);
    $(document).on("submit", ".delete-form", function (e) {
        e.preventDefault();
        let form = $(this);

        if (confirm("Are you sure you want to delete this source?")) {
            $.ajax({
                url: form.attr("action"),
                type: "POST",
                data: form.serialize(),
                success: function () {
                    fetchSources();  // Refresh table after deletion
                },
                error: function (xhr) {
                    console.error("Error deleting source:", xhr.responseText);
                    alert("Failed to delete source.");
                }
            });
        }
    });
});

function fetchSources(page=1) {
        $.ajax({
            url: sourceListUrl,
            data: {q: $("#search-source").val().trim()},
            dataType: "json",
            success: function (response) {
                let sourceTableBody = $("#source-table tbody");
                sourceTableBody.empty();

                if (!response.sources || response.sources.length === 0) {
                    sourceTableBody.append("<tr><td colspan='4'>No results found.</td></tr>");
                    return;
                }

                response.sources.forEach(source => {
                    let companies = source.tagged_companies.length
                        ? source.tagged_companies.join(", ")
                        : "N/A";

                    sourceTableBody.append(`
                        <tr class="source-row">
                            <td class="source-name">${source.name}</td>
                            <td><a href="${source.url}" target="_blank">${source.url}</a></td>
                            <td>${companies}</td>
                            <td>
                                <a href="/source/fetch-story/${source.id}/" class="edit-btn">Fetch Story</a>
                                <a href="/source/edit/${source.id}/" class="edit-btn">Edit</a>
                                <form action="/source/delete/${source.id}/" method="post" class="delete-form">
                                    <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                                    <button type="submit" class="delete-btn" onclick="return confirm('Are you sure?');">Delete</button>
                                </form>

                            </td>
                        </tr>`);
//                    sourceTableBody.append(rowHtml);
                });
                updatePagination(response);
            },
            error: function (xhr) {
                console.error("Error fetching sources:", xhr.responseText);
                alert("Failed to load sources. Please check your connection.");
            }
        });
    }

function fetchStories() {
        let sourceId = $(this).data("source-id");
        let finalUrl = fetchStoriesUrl + sourceId + "/";

        $.ajax({
            url: finalUrl,
            method: "POST",
            headers: { "X-CSRFToken": csrfToken },
            success: function (response) {
                $("#fetch-message").text(response.message).show().delay(3000).fadeOut();
            },
            error: function (xhr) {
                console.error("Error fetching story:", xhr.responseText);
                alert("Failed to fetch story. Please try again.");
            }
        });
    }
