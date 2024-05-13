import { getCookie } from "./get_cookie.js";
import { addCommentToHTML } from "./add_comment_to_html.js";

document
	.getElementById("posts-container")
	.addEventListener("click", (event) => {
		if (
			event.target.tagName === "BUTTON" &&
			event.target.hasAttribute("data-post-id")
		) {
			const authorId = document
				.getElementById("user-info")
				.getAttribute("comment-author-id");
			const postId = event.target.getAttribute("data-post-id");
			const commentContent = document.getElementById(`comment-${postId}`);
			postComment(authorId, postId, commentContent.value);
			commentContent.value = "";
		}
	});

function postComment(authorId, postId, commentContent) {
	if (typeof postId === "undefined") {
		console.error("postId is undefined");
		return;
	}

	const csrftoken = getCookie("csrftoken");
	fetch(`/api2/comments/add/${postId}`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			"X-CSRFToken": csrftoken,
		},
		body: JSON.stringify({
			author: authorId,
			content: commentContent,
			post: postId,
		}),
	})
		.then((response) =>
			response.ok ? response.json() : Promise.reject(response),
		)
		.then((data) => {
			console.log("Comment posted:", data);
			addCommentToHTML(data);
		})
		.catch((error) => {
			console.error("Error posting comment:", error);
		});
}

window.postComment = postComment;
