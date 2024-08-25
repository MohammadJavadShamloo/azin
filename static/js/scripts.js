document.addEventListener('DOMContentLoaded', function () {
    const chatTab = document.getElementById('chat-tab');
    const chatToggle = document.getElementById('chat-toggle');
    const chatContent = document.getElementById('chat-content');
    const messageInput = document.getElementById('message-input');
    const sendMessageButton = document.getElementById('send-message');
    const chatMessages = document.getElementById('chat-messages');
    const recipientSelect = document.getElementById('recipient');

    let socket = null;

    // Toggle chat window visibility
    chatToggle.addEventListener('click', function () {
        chatContent.classList.toggle('d-none');
    });

    // Connect to WebSocket when a recipient is selected
    recipientSelect.addEventListener('change', function () {
        if (socket) {
            socket.close();
        }

        const roomName = recipientSelect.value;

        socket = new WebSocket(
            `ws://${window.location.host}/ws/chat/${roomName}/`
        );

        socket.onmessage = function (e) {
            const data = JSON.parse(e.data);
            const message = data['message'];
            chatMessages.innerHTML += `<div>${message}</div>`;
            chatMessages.scrollTop = chatMessages.scrollHeight;
        };

        socket.onclose = function (e) {
            console.error('Chat socket closed unexpectedly');
        };
    });

    // Send message
    sendMessageButton.addEventListener('click', function () {
        const message = messageInput.value;
        if (message && socket) {
            socket.send(JSON.stringify({
                'message': message
            }));
            messageInput.value = '';
        }
    });
});
