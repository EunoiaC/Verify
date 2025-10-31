chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "SEND_TITLE") {
        console.log("[Extension Background] Received title request:", message);

        fetch("http://127.0.0.1:5000/receive", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                id: message.id,
                title: message.title,
                body: message.body || ""
            })
        })
        .then(res => res.text())  // get raw text first
        .then(text => {
            let data;
            try {
                data = JSON.parse(text);  // try parse as JSON
            } catch (e) {
                console.warn("[Extension Background] Response is not valid JSON:", text);
                data = { raw: text };
            }
            console.log("[Extension Background] Server response:", data);
            sendResponse({ ok: true, data });
        })
        .catch(err => {
            console.error("[Extension Background] Error sending to server:", err);
            sendResponse({ ok: false, error: err.toString() });
        });

        return true; // keep message channel open
    }
});
