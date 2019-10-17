const room_name = document.querySelector("#room_name").value;
const chats = document.querySelector(".chat-list")
const message_field = document.querySelector("#message")
const username = document.querySelector("#username").value;
const send_btn = document.querySelector("#send");

message.addEventListener("keyup", (e)=>{
    if(e.key=="Enter"){
        send_btn.click();
        message.value = ""
        message.blur();
    }
})


chats.scrollBy(0, chats.scrollHeight)

document.addEventListener("DOMContentLoaded", ()=>{
    const connection_namespace = `${location.protocol}//${document.domain}:${location.port}/chat/${room_name}/socket`;

    var socket = io.connect(connection_namespace);

    socket.on('connect', ()=>{
        send_btn.addEventListener("click", (e)=>{
            e.preventDefault();
            var message = document.querySelector("#message").value;

            socket.emit("message_send", {"message": message, "room_name": room_name, "username": username})
        })
    })

    socket.on("message_receive", data=>{

        var message = data.message;
        var sender = data.sender;

        var message_div = document.createElement("div");
        message_div.setAttribute("class", "message");

        var message_name = document.createElement("div");
        message_name.setAttribute("class", "message-name");
        message_name.innerHTML = sender;

        var message_text_div = document.createElement("div");
        message_text_div.setAttribute("class", "message-text");
        message_text_div.innerHTML = message;

        message_div.appendChild(message_name)
        message_div.append(message_text_div)

        chats.appendChild(message_div)

        chats.scrollBy(0, chats.scrollHeight)

    })



})