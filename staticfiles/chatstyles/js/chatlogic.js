$(document).ready(function(){
    // Function to format and append messages
    function appendMessage(role, content) {
        let emoji = role === 'assistant' ? '<img src="/static/chatstyles/images/wwlavp.jpg" alt="Assistant">' : '<img src="/static/chatstyles/images/user-small-boi.svg" alt="User">';
        $('#messages').append(`<li class="${role}">${emoji} ${content}</li>`);
        scrollToBottom();
    }
    
    // Function to handle form submission
    $('#chat-form').on('submit', function(e){
        e.preventDefault();

        let userMessage = $('#message').val().trim().toLowerCase();

        if (userMessage === '') {
            alert('Please enter a message.');
            return;
        }

        appendMessage('user', userMessage);
        showTypingMessage(); // Show typing indicator

        $.ajax({
            url: '/chat/',
            type: 'POST',
            data: {
                'message': userMessage,
                'csrfmiddlewaretoken': '{{ csrf_token }}'
            },
            success: function(response){
                hideTypingMessage(); // Hide typing indicator
                if (userMessage.includes('hi') || userMessage.includes('hello')) {
                    appendMessage('assistant', `${getGreeting()} How can I assist you today?`);
                } else {
                    appendMessage('assistant', response.message);
                }
            },
            error: function(response){
                hideTypingMessage(); // Hide typing indicator
                alert('Error: ' + response.responseJSON.error);
            }
        });

        $('#message').val('');
    });

    // Function to show typing indicator
    function showTypingMessage() {
        $('#messages').append('<li class="assistant typing"><img src="/static/chatstyles/images/wwlavp.jpg" alt="Assistant"> Assistant is typing...</li>');
        scrollToBottom();
    }

    // Function to hide typing indicator
    function hideTypingMessage() {
        $('.typing').remove();
    }

    // Function to get greeting based on time of day
    function getGreeting() {
        const now = new Date();
        const hour = now.getHours();

        if (hour < 12) {
            return "Good morning!";
        } else if (hour < 18) {
            return "Good afternoon!";
        } else {
            return "Good evening!";
        }
    }

    // Function to scroll to the bottom of the messages container
    function scrollToBottom() {
        $('#messages').scrollTop($('#messages')[0].scrollHeight);
    }

    // Initial greeting message
    $(window).on('load', function(){
        appendMessage('assistant', `${getGreeting()} Welcome!`);
    });
});
