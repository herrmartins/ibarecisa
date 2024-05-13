import { getCookie } from "./get_cookie.js";

document
	.getElementById("posts-container")
	.addEventListener("click", (event) => {
		if (event.target.classList.contains("bi-chat-left-dots")) {
			const postId = event.target.getAttribute("data-post-id");
			loadComments(postId);
		}
	});

function loadComments(postId) {
	const commentsContainer = document.getElementById(`comments-${postId}`);
	const form = document.getElementById(`form-${postId}`);
	if (!commentsContainer.classList.contains("hidden")) {
		commentsContainer.classList.add("hidden");
		form.classList.add("hidden");
	} else {
		commentsContainer.classList.remove("hidden");
		form.classList.remove("hidden");
	}

	if (commentsContainer.innerHTML.trim() === "") {
		fetch(`/api2/comments/${postId}`)
			.then((response) => response.json())
			.then((comments) => {
				console.log("Comentários", comments);
				if (comments.length > 0) {
					const commentElements = comments
						.map(
							(comment) => `
            <div class="card ml-2 my-2 p-2 card-no-border">
              <div class="card-body">
                <p class="card-text">${comment.content}</p>
                <div class="d-flex justify-content-between">
                  <div class="d-flex flex-row align-items-center">
                    ${
											comment.user_photo
												? `<img src="${comment.user_photo}" alt="avatar" width="25" height="25" />`
												: ""
										}
                    <p class="small mb-0 ms-2">${comment.author_name}</p>
                  </div>
                  <div class="d-flex flex-row align-items-center">
                    <p class="small text-muted mb-0">Like</p>
                    <i class="bi bi-hand-thumbs-up" style="margin-top: -0.16rem;"></i>
                  </div>
                </div>
              </div>
            </div>
          `,
						)
						.join("");

					commentsContainer.innerHTML = commentElements;
				} else {
					const noCommentsMsg = document.createElement("p");
					noCommentsMsg.textContent = "Seja o primeiro a comentar...";
					commentsContainer.appendChild(noCommentsMsg);
					setTimeout(() => {
						noCommentsMsg.style.display = "none";
					}, 3000);
				}
			})
			.catch((error) => {
				console.error("Error fetching comments:", error);
			});
	}
}
