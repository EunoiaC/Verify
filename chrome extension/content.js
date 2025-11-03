console.log("[Extension] Content script loaded");

const processedPosts = new Set();

// idk how to use the utils.js one
function generateId() {
    return "post-" + Math.random().toString(36).substring(2, 15);
}

//styling
function customStyles() {
    const css = `
    .shreddit-verify-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 10px;
        background: #0079d3;
        color: #fff;
        border-radius: 6px;
        border: none;
        font-weight: 600;
        font-size: 13px;
        line-height: 1;
        cursor: pointer;
        box-shadow: 0 1px 0 rgba(0,0,0,0.25);
        transition: background-color 120ms ease, transform 60ms ease;
        vertical-align: middle;
        user-select: none;
    }
    .shreddit-verify-btn:hover { background: #1491ff; }
    .shreddit-verify-btn:active { transform: translateY(1px); }
    .shreddit-verify-btn svg { width: 14px; height: 14px; fill: currentColor; display: inline-block; vertical-align: middle; }
    `;
    const style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);
}

customStyles();

function processTitles() {
    console.log("[Extension] Scanning for title elements");

    const titles = document.querySelectorAll('[slot="title"]');
    console.log("[Extension] Found title count:", titles.length);

    titles.forEach(titleEl => {
        const shredditPost = titleEl.closest("shreddit-post");
        if (!shredditPost) {
            console.log("[Extension] No shreddit-post parent found");
            return;
        }

        if (processedPosts.has(shredditPost)) {
            console.log("[Extension] Already processed, skipping");
            return;
        }

        processedPosts.add(shredditPost);

        let titleText = titleEl.textContent.trim();

        // check for text-body element
        const textBody = shredditPost.querySelector('[slot="text-body"]');
        let bodyText = "";
        if (textBody) {
            bodyText = textBody.textContent.trim();
            console.log("[Extension] Text body found");
        }

        const postId = generateId();

        titleEl.dataset.uniqueId = postId;
        console.log("[Extension] Assigned ID:", postId, "Title:", titleText, "Body:", bodyText);

        const button = document.createElement("button");
        button.type = "button";
        button.className = "shreddit-verify-btn";
        button.setAttribute("aria-label", "Verify post");
        button.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4z"/></svg><span>Verify</span>`;

        button.addEventListener("click", () => {
            console.log("[Extension] Verify clicked for", postId);

            chrome.runtime.sendMessage(
                {
                    type: "SEND_TITLE",
                    id: postId,
                    title: titleText,
                    body: bodyText
                },
                response => {
                    console.log("[Extension] Background script responded:", response);
                    if (response.data) {
                        let analysis = response.data.analysis;
                        let processed = {};

                        for (let i = 0; i < analysis.length; i++) {
                            let item = analysis[i];
                            let claim = item.claim;
                            let source = item.source_url;
                            let span = item.span;
                            let results = item.results;

                            if (!(claim in processed)) {
                                processed[claim] = {
                                    span: span,
                                    claim: claim,
                                    results: []
                                };
                            }
                            for (let j = 0; j < results.length; j++) {
                                let result = results[j];
                                processed[claim].results.push({
                                    ...result,
                                    source
                                });
                            }
                        }
                        console.log("[Extension] Processed analysis:", processed);

                        // create and insert analysis log
                        const analysisLog = createAnalysisLog(processed, shredditPost);
                        shredditPost.insertAdjacentElement("afterend", analysisLog);

                        // highlight spans for each claim
                        for (let claim in processed) {
                            let claimData = processed[claim];
                            let span = claimData.span;
                            let results = claimData.results;

                            let supportCount = results.filter(r => r.label === "entailment").length;
                            let contradictCount = results.filter(r => r.label === "contradiction").length;

                            let highlightColor = "#B8860B";
                            if (!(supportCount > 0 && contradictCount > 0)) {
                                if (supportCount > contradictCount && supportCount > 0) {
                                    highlightColor = "#007B7F";
                                } else if (contradictCount > supportCount && contradictCount > 0) {
                                    highlightColor = "#8E2DE2";
                                }
                            }

                            highlightSpan(span, titleEl, bodyText ? shredditPost.querySelector('[slot="text-body"]') : null, highlightColor, claimData, results);
                        }
                    }
                }
            );
        });

        shredditPost.insertAdjacentElement("afterend", button);
        console.log("[Extension] Button inserted after post");
    });
}

function highlightSpan(span, titleEl, bodyEl, color, claimData, results) {
    // search in title
    let found = highlightInElement(span, titleEl, color, claimData, results);

    // search in body if not found
    if (!found && bodyEl) {
        highlightInElement(span, bodyEl, color, claimData, results);
    }
}


function highlightInElement(span, element, color, claimData, results) {
    const fullText = element.textContent;
    const index = fullText.indexOf(span);
    if (index === -1) return false;

    // find start and end containers for the range
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
    let node;
    let currentOffset = 0;
    let startNode = null, startOffset = 0, endNode = null, endOffset = 0;
    const endIndex = index + span.length;

    while ((node = walker.nextNode())) {
        const nodeLen = node.nodeValue.length;
        if (!startNode && currentOffset + nodeLen > index) {
            startNode = node;
            startOffset = index - currentOffset;
        }
        if (currentOffset + nodeLen >= endIndex) {
            endNode = node;
            endOffset = endIndex - currentOffset;
            break;
        }
        currentOffset += nodeLen;
    }

    if (!startNode || !endNode) return false;

    const range = document.createRange();
    range.setStart(startNode, startOffset);
    range.setEnd(endNode, endOffset);

    // highlight element and attach handlers
    const highlightEl = document.createElement("span");
    highlightEl.textContent = range.toString();
    //visual styles (do not overwrite complex layout)
    highlightEl.style.cursor = "pointer";
    highlightEl.style.padding = "2px 4px";
    highlightEl.style.borderRadius = "2px";
    if (color) highlightEl.style.backgroundColor = color;

    highlightEl.addEventListener("mouseenter", (e) => {
        showPopup(e, claimData, results, color);
    });
    highlightEl.addEventListener("mouseleave", () => {
        removePopup();
    });

    // Replace the range contents with the highlight element
    try {
        range.deleteContents();
        range.insertNode(highlightEl);
    } catch (err) {
        console.error("[Extension] Failed to apply highlight range:", err);
        return false;
    }

    return true;
}

function createAnalysisLog(processed, shredditPost) {
    const analysisContainer = document.createElement("div");
    analysisContainer.style.marginTop = "12px";
    analysisContainer.style.padding = "12px";
    analysisContainer.style.backgroundColor = "#1a1a1b";
    analysisContainer.style.borderLeft = "4px solid #818384";
    analysisContainer.style.borderRadius = "4px";
    analysisContainer.style.fontFamily = "Arial, sans-serif";
    analysisContainer.style.fontSize = "13px";

    const title = document.createElement("strong");
    title.textContent = "Fact Check Analysis";
    title.style.display = "block";
    title.style.marginBottom = "8px";
    title.style.color = "#d7dadc";
    analysisContainer.appendChild(title);

    for (let claim in processed) {
        const claimData = processed[claim];
        const results = claimData.results;

        const claimEntry = document.createElement("div");
        claimEntry.style.marginBottom = "10px";
        claimEntry.style.padding = "10px";
        claimEntry.style.backgroundColor = "#272729";
        claimEntry.style.borderRadius = "3px";
        claimEntry.style.borderLeft = "3px solid #818384";

        let html = `<div style="margin-bottom: 8px;">`;
        html += `<strong style="color: #d7dadc;">"${claimData.claim}"</strong><br>`;
        html += `<span style="color: #818384; font-size: 12px;">Span: ${claimData.span}</span>`;
        html += `</div>`;

        html += `<div style="display: flex; flex-wrap: wrap; gap: 6px;">`;
        results.forEach((result, idx) => {
            let labelColor = "#818384";
            if (result.label === "entailment") {
                labelColor = "#007B7F";
            } else if (result.label === "contradiction") {
                labelColor = "#8E2DE2";
            }

            html += `<div style="cursor: pointer; padding: 4px 8px; background: ${labelColor}; color: white; border-radius: 3px; font-size: 11px; font-weight: bold; user-select: none;" class="verdict-tag" data-claim="${claim}" data-index="${idx}">`;
            html += `${result.label.toUpperCase()}`;
            html += `</div>`;
        });
        html += `</div>`;

        claimEntry.innerHTML = html;
        analysisContainer.appendChild(claimEntry);
    }

    // add click handlers for verdict tags
    analysisContainer.querySelectorAll(".verdict-tag").forEach(tag => {
        tag.addEventListener("click", (e) => {
            const claim = e.target.dataset.claim;
            const index = parseInt(e.target.dataset.index);
            const result = processed[claim].results[index];
            showVerdictDetails(e, result);
        });
    });

    return analysisContainer;
}

function showVerdictDetails(event, result) {
    removePopup();

    const popup = document.createElement("div");
    popup.id = "claim-popup";
    popup.style.position = "fixed";
    popup.style.backgroundColor = "#1a1a1b";
    popup.style.border = "1px solid #818384";
    popup.style.borderRadius = "4px";
    popup.style.padding = "12px";
    popup.style.zIndex = "10000";
    popup.style.maxWidth = "350px";
    popup.style.boxShadow = "0 4px 12px rgba(0,0,0,0.5)";
    popup.style.fontSize = "12px";
    popup.style.fontFamily = "Arial, sans-serif";
    popup.style.color = "#d7dadc";

    let labelColor = "#818384";
    if (result.label === "entailment") {
        labelColor = "#4caf50";
    } else if (result.label === "contradiction") {
        labelColor = "#ff6b6b";
    }

    let html = `<div style="margin-bottom: 8px;">`;
    html += `<strong style="color: ${labelColor}; font-size: 14px;">${result.label.toUpperCase()}</strong>`;
    html += `</div>`;

    html += `<div style="background: #272729; padding: 8px; border-radius: 3px; margin-bottom: 8px;">`;
    html += `<strong style="color: #818384; font-size: 11px;">CONTEXT</strong><br>`;
    html += `<span style="color: #d7dadc;">${result.context}</span>`;
    html += `</div>`;

    html += `<a href="${result.source}" target="_blank" style="color: #818384; text-decoration: none; display: inline-block; padding: 6px 10px; background: #272729; border-radius: 3px; border: 1px solid #818384; transition: all 0.2s;">Source URL</a>`;

    popup.innerHTML = html;
    document.body.appendChild(popup);

    const rect = event.target.getBoundingClientRect();
    let left = rect.left;
    let top = rect.bottom + 5;

    if (left + 350 > window.innerWidth) {
        left = window.innerWidth - 370;
    }
    if (top + popup.offsetHeight > window.innerHeight) {
        top = rect.top - popup.offsetHeight - 5;
    }

    popup.style.left = left + "px";
    popup.style.top = top + "px";

    // close popup when clicking outside
    document.addEventListener("click", closePopupOnClickOutside);
}

function closePopupOnClickOutside(e) {
    const popup = document.getElementById("claim-popup");
    if (popup && !popup.contains(e.target) && !e.target.classList.contains("verdict-tag")) {
        removePopup();
        document.removeEventListener("click", closePopupOnClickOutside);
    }
}

function showPopup(event, claimData, results, color) {
    removePopup();

    const popup = document.createElement("div");
    popup.id = "claim-popup";
    popup.style.position = "fixed";
    popup.style.backgroundColor = "#1a1a1b";
    popup.style.border = "1px solid #818384";
    popup.style.borderRadius = "4px";
    popup.style.padding = "12px";
    popup.style.zIndex = "10000";
    popup.style.maxWidth = "350px";
    popup.style.boxShadow = "0 4px 12px rgba(0,0,0,0.5)";
    popup.style.fontSize = "12px";
    popup.style.fontFamily = "Arial, sans-serif";
    popup.style.color = "#d7dadc";

    let html = `<strong style="color: #d7dadc;">Claim:</strong> ${claimData.claim}<br><br>`;
    html += `<strong style="color: #d7dadc;">Results:</strong><br>`;

    results.forEach(result => {
        let labelColor = "#818384";
        if (result.label === "entailment") {
            labelColor = "#4caf50";
        } else if (result.label === "contradiction") {
            labelColor = "#ff6b6b";
        }

        html += `<div style="margin: 8px 0; padding: 8px; background: #272729; border-left: 2px solid ${labelColor}; border-radius: 2px;">`;
        html += `<strong style="color: ${labelColor};">${result.label.toUpperCase()}</strong><br>`;
        html += `<span style="color: #818384; font-size: 11px;">Context:</span> <span style="color: #d7dadc;">${result.context.substring(0, 100)}...</span><br>`;
        html += `<a href="${result.source}" target="_blank" style="color: #818384; text-decoration: underline;">Source</a>`;
        html += `</div>`;
    });

    popup.innerHTML = html;
    document.body.appendChild(popup);

    const rect = event.target.getBoundingClientRect();
    let left = rect.left;
    let top = rect.bottom + 5;

    if (left + 350 > window.innerWidth) {
        left = window.innerWidth - 370;
    }
    if (top + popup.offsetHeight > window.innerHeight) {
        top = rect.top - popup.offsetHeight - 5;
    }

    popup.style.left = left + "px";
    popup.style.top = top + "px";
}


function removePopup() {
    const existingPopup = document.getElementById("claim-popup");
    if (existingPopup) {
        existingPopup.remove();
    }
}


// initial scan
processTitles();

// infinite scroll
const observer = new MutationObserver(() => {
    console.log("[Extension] DOM changed, rescanning");
    processTitles();
});

observer.observe(document.body, {childList: true, subtree: true});
