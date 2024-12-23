document.addEventListener("DOMContentLoaded", function () {
  const sendButton = document.getElementById("send-btn");
  const userInput = document.getElementById("user-input");
  const chatContainer = document.getElementById("chat-container");

  // Function to send message to the backend
  function sendMessageToServer(message) {
      const sessionId = localStorage.getItem("session_id") || generateSessionId();
      localStorage.setItem("session_id", sessionId);

      fetch("/chat", {
          method: "POST",
          headers: {
              "Content-Type": "application/json"
          },
          body: JSON.stringify({
              message: message,
              session_id: sessionId
          })
      })
      .then(response => response.json())
      .then(data => {
          const botMessage = data.response;
          appendMessage(botMessage, "bot");  // Append bot response
      })
      .catch(error => {
          console.error("Error sending message to server:", error);
      });
  }

  // Function to append a message to the chat window
  function appendMessage(message, sender) {
      const messageDiv = document.createElement("div");
      messageDiv.classList.add("message");
      messageDiv.classList.add(sender === "user" ? "user-message" : "bot-message");
      messageDiv.textContent = message;
      chatContainer.appendChild(messageDiv);

      // Scroll to the latest message
      chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  // Function to generate a unique session ID
  function generateSessionId() {
      return "session_" + Math.random().toString(36).substr(2, 9);
  }

  // Send message when 'Enter' key is pressed in the input field
  userInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
          e.preventDefault();  // Prevent form submission or any other default behavior
          const message = userInput.value.trim();
          if (message) {
              appendMessage(message, "user");
              sendMessageToServer(message);
              userInput.value = "";  // Clear the input field
          }
      }
  });

  // Send message when the 'Send' button is clicked
  sendButton.addEventListener("click", function () {
      const message = userInput.value.trim();
      if (message) {
          appendMessage(message, "user");
          sendMessageToServer(message);
          userInput.value = "";  // Clear the input field
      }
  });
});
