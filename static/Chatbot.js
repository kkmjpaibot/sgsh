(function(){
    const chat = document.getElementById('chat');
    const input = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');

    // -----------------------
    // Helpers
    // -----------------------
    function parseOptions(text){
        const lines = text.split('\n');
        const optionRegex = /^\s*(\d+)[\.\)]\s*(.+)$/;
        const options = [];
        const other = [];
        for(const line of lines){
            const m = line.match(optionRegex);
            if(m){
                options.push({key: m[1], label: m[2].trim()});
            } else {
                other.push(line);
            }
        }
        return {message: other.join('\n').trim(), options};
    }
    // Escape HTML to avoid XSS
    function escapeHtml(str){
        return (str || '').toString()
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // Convert plaintext URLs to clickable, safe anchor tags
    function linkify(text){
        let t = escapeHtml(text);
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        return t.replace(urlRegex, function(url){
            return '<a href="' + url + '" target="_blank" rel="noopener noreferrer">' + url + '</a>';
        });
    }
    function lockTyping(message){
        input.disabled = true;
        sendBtn.disabled = true;
        input.placeholder = message || "Please select an option above";
    }

    function unlockTyping(){
        input.disabled = false;
        sendBtn.disabled = false;
        input.placeholder = "Type your message...";
        input.focus();
    }

    // -----------------------
    // Append messages
    // -----------------------
    function appendMessage(message, sender='bot'){
        const el = document.createElement('div');
        el.className = `message ${sender}`;

        const meta = document.createElement('span');
        meta.className = 'meta';
        meta.textContent = sender === 'bot' ? 'Erica (Agent)' : 'You';

        const body = document.createElement('div');
        body.className = 'body';
        body.style.whiteSpace = 'pre-line';

        if(sender === 'bot'){
            const parsed = parseOptions(message);
            const display = parsed.message || (parsed.options.length ? '' : message);
            // Use linkify to render clickable URLs in bot messages, safely
            body.innerHTML = display ? linkify(display) : '';
            el.appendChild(meta);
            el.appendChild(body);

            if(parsed.options.length){
                const optsWrap = document.createElement('div');
                optsWrap.className = 'options';
                parsed.options.forEach(opt=>{
                    const b = document.createElement('button');
                    b.className = 'option-btn';
                    b.type = 'button';
                    b.innerText = `${opt.key}. ${opt.label}`;
                    b.dataset.value = opt.key;
                    b.addEventListener('click', function(){ sendChoice(opt.key, opt.label, b); });
                    optsWrap.appendChild(b);
                });
                el.appendChild(optsWrap);
                lockTyping("Please select an option above");
            } else {
                // Unlock typing for free-text responses (income, phone, email)
                unlockTyping();
            }
        } else {
            // Keep user messages as textContent to avoid accidental HTML rendering
            body.textContent = message;
            el.appendChild(meta);
            el.appendChild(body);
        }

        chat.appendChild(el);
        chat.scrollTop = chat.scrollHeight;
    }

    // -----------------------
    // Restart button helpers
    // -----------------------
    function showRestartButton(){
        // show only the inline restart control
        showInlineRestartButton();
    }

    function hideRestartButton(){
        // hide only the inline restart control
        hideInlineRestartButton();
    }

    function showInlineRestartButton(){
        const inline = document.getElementById('restartInlineBtn');
        if(inline){
            inline.removeAttribute('hidden');
            inline.disabled = false;
            try{ inline.focus(); }catch(e){}
        }
        // Disable typing and send button and set helpful placeholder
        lockTyping('Click Restart to start a new conversation');
    }

    function hideInlineRestartButton(){
        const inline = document.getElementById('restartInlineBtn');
        if(inline){
            inline.setAttribute('hidden','');
            inline.disabled = false;
        }
        // Re-enable typing area
        unlockTyping();
    }

    // -----------------------
    // Typing indicator
    // -----------------------
    function setTyping(on=true){
        let t = document.querySelector('.typing');
        if(on){
            if(!t){
                t = document.createElement('div');
                t.className = 'message bot typing';
                t.textContent = 'Erica is typing...';
                chat.appendChild(t);
                chat.scrollTop = chat.scrollHeight;
            }
        } else {
            if(t) t.remove();
        }
    }

    function shouldKeepSingle(reply){
        if(!reply) return false;
        const keyPhrases = [
            'Your Personalised Income Protection Plan',
            '📝',
            'Years of Coverage',
            'Recommended Coverage',
            'Premium Rate',
            'Monthly Premium',
            '--------------------------------',
            'https://wa.me/'
        ];
        const text = reply.toString();
        return keyPhrases.some(p => text.indexOf(p) !== -1);
    }

    function splitIntoTwo(text){
        text = (text || '').toString().trim();
        if(!text) return ['', ''];

        // If there are explicit double-newlines, use the first block as part 1 and the rest as part 2
        const blocks = text.split(/\n{2,}/);
        if(blocks.length >= 2){
            return [blocks[0].trim(), blocks.slice(1).join('\n\n').trim()];
        }

        // If there's a single newline, split at the first newline
        const firstNl = text.indexOf('\n');
        if(firstNl !== -1){
            return [text.slice(0, firstNl).trim(), text.slice(firstNl+1).trim()];
        }

        // Otherwise, split near the middle at a sentence boundary or space
        const mid = Math.floor(text.length / 2);
        const punctMatch = /[\.\!\?]/g;
        // search for punctuation near middle
        const searchRadius = Math.min(60, Math.floor(text.length / 6));
        let best = -1;
        for(let i = Math.max(0, mid - searchRadius); i < Math.min(text.length, mid + searchRadius); i++){
            if(/[\.\!\?]/.test(text[i])){ best = i; break; }
        }
        let splitIdx = -1;
        if(best !== -1) splitIdx = best + 1;
        if(splitIdx === -1){
            const left = text.lastIndexOf(' ', mid);
            const right = text.indexOf(' ', mid + 1);
            if(left !== -1 && (mid - left) <= (right - mid || Infinity)) splitIdx = left;
            else if(right !== -1) splitIdx = right;
            else splitIdx = mid;
        }
        return [text.slice(0, splitIdx).trim(), text.slice(splitIdx).trim()];
    }

    function handleServerReply(reply){
        reply = reply || '';
        // Ensure common email prompt phrasings appear as their own bubble
        const emailPrompts = [
            'May I have your email address to send you more details?',
            'Please type your email address, we will send you an email summary of our conversation for your reference',
            'Please type your email address'
        ];

        for(const emailPrompt of emailPrompts){
            let idx = reply.indexOf(emailPrompt);
            while(idx !== -1){
                if(idx > 0){
                    const before = reply.slice(0, idx);
                    if(!before.endsWith('\n\n')){
                        reply = before.trimEnd() + '\n\n' + reply.slice(idx).trimStart();
                        idx = reply.indexOf(emailPrompt, idx + emailPrompt.length + 2);
                    } else {
                        idx = reply.indexOf(emailPrompt, idx + emailPrompt.length);
                    }
                } else {
                    idx = reply.indexOf(emailPrompt, idx + emailPrompt.length);
                }
            }
        }

        // If the reply contains multiple explicit double-newlines, split into multiple bubbles
        const explicitParts = reply.split(/\n{2,}/).map(p=>p.trim()).filter(Boolean);
        const finalMarkers = [
            'Great! Thank you for signing up.',
            'If you want to calculate again',
            'Thank you for contacting us.'
        ];

        if(explicitParts.length >= 3){
            explicitParts.forEach((part, i)=> setTimeout(()=> appendMessage(part, 'bot'), i*400));
            if(finalMarkers.some(m => reply.indexOf(m) !== -1)){
                setTimeout(()=> showRestartButton(), explicitParts.length * 400 + 200);
            }
            return;
        }

        // If there are exactly two explicit parts, show them as two bubbles
        if(explicitParts.length === 2){
            appendMessage(explicitParts[0], 'bot');
            setTimeout(()=> appendMessage(explicitParts[1], 'bot'), 400);
            if(finalMarkers.some(m => reply.indexOf(m) !== -1)){
                setTimeout(()=> showRestartButton(), 400 * 2 + 200);
            }
            return;
        }

        // Fallback: split into two natural parts (for small/one-line replies)
        const parts = splitIntoTwo(reply);
        const first = (parts[0] || '').trim();
        const second = (parts[1] || '').trim();

        if(first) appendMessage(first, 'bot');
        if(second) setTimeout(()=> appendMessage(second, 'bot'), 400);

        if(finalMarkers.some(m => reply.indexOf(m) !== -1)){
            // show after the messages finish displaying
            setTimeout(()=> showRestartButton(), second ? 900 : 400);
        }
    }

    const TAB_KEY = 'sgsh_chat_tab_id';
    function getTabId(){
        let id = sessionStorage.getItem(TAB_KEY);
        if(!id){
            id = 'tab_' + Date.now() + '_' + Math.random().toString(36).slice(2,9);
            sessionStorage.setItem(TAB_KEY, id);
        }
        return id;
    }

    // -----------------------
    // Send message to server
    // -----------------------
    function sendToServer(message){
        setTyping(true);
        lockTyping("Erica is typing...");

        return fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({message, tab_id: getTabId()})
        }).then(r=>r.json()).then(data=>{
            return new Promise(resolve=>{
                setTimeout(()=>{
                    setTyping(false);
                    resolve(data.reply);
                }, 1500); // slightly faster typing delay
            });
        }).catch(err=>{
            setTyping(false);
            console.error(err);
            unlockTyping();
            return 'Sorry, something went wrong connecting to the server.';
        });
    }

    // -----------------------
    // Send option choice
    // -----------------------
    function sendChoice(value, label, btn){
        hideRestartButton();
        hideInlineRestartButton();
        const container = btn && btn.closest('.options');
        if(container){
            container.querySelectorAll('button').forEach(b=> b.disabled = true);
        }

        appendMessage(label || value, 'user');
        lockTyping("Erica is typing...");

        sendToServer(value).then(reply=>{
            handleServerReply(reply);
        });
    }

    // -----------------------
    // Send typed message
    // -----------------------
    function sendMessage(){
        hideRestartButton();
        hideInlineRestartButton();
        const text = input.value.trim();
        if(!text) return;

        appendMessage(text, 'user');
        input.value = '';
        autoResize();

        lockTyping("Erica is typing...");

        sendToServer(text).then(reply=>{
            handleServerReply(reply);
        });
    }

    function autoResize(){
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 140) + 'px';
    }

    function initialGreeting(){
        hideRestartButton();
        hideInlineRestartButton();
        sendToServer('').then(reply=>{
            handleServerReply(reply);
        }).catch(err=>{
            appendMessage('Unable to reach server for initial greeting.', 'bot');
            console.error(err);
        });
    }

    // -----------------------
    // Event listeners
    // -----------------------
    document.addEventListener('DOMContentLoaded', function(){
        sessionStorage.removeItem(TAB_KEY);
        initialGreeting();
        input.focus();



        const inlineRestart = document.getElementById('restartInlineBtn');
        if(inlineRestart){
            inlineRestart.addEventListener('click', function(){
                inlineRestart.disabled = true;
                fetch('/reset', {
                    method: 'POST',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({tab_id: getTabId()})
                }).then(r=>r.json()).then(()=>{
                    chat.innerHTML = '';
                    initialGreeting();
                }).catch(err=>console.error(err))
                  .finally(()=> inlineRestart.disabled = false);
            });
        }

        sendBtn.addEventListener('click', sendMessage);
        input.addEventListener('keydown', function(e){
            if(e.key === 'Enter' && !e.shiftKey){
                e.preventDefault();
                sendMessage();
            }
        });
        input.addEventListener('input', autoResize);
    });

})();
