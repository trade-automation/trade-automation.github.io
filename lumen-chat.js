/**
 * Lumen Chat Widget v1.0
 * Self-contained chat widget for foshanFFE.com
 * Zero third-party dependencies
 * Integrates Lumen knowledge base for auto-responses
 */
(function() {
  'use strict';

  // ===== Lumen Knowledge Base =====
  var KB = {
    greetings: {
      keywords: ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings'],
      response: "Welcome to Foshan FF&E Solutions! We're a hospitality FF&E integrator specializing in full guestroom and public-area packages for 4-5 star hotels. How can we help you today?"
    },
    company: {
      keywords: ['who are you', 'about', 'company', 'your company', 'tell me about', 'your background'],
      response: "Foshan FF&E Solutions is a hospitality FF&E integrator based in Foshan, China. We specialize in full guestroom and public-area packages for 4-5 star hotels, managing 19 specialized factories under a single PO. We hold UL, CARB P2, BS 7177, UAE Civil Defence, EN 16798-2, and ISO 9001:2015 certifications. Recent projects include deliveries for Marriott, Hilton, IHG, Accor, Radisson, and Wyndham across the Middle East and North America."
    },
    services: {
      keywords: ['what do you do', 'services', 'products', 'offer', 'provide', 'supply', 'categories'],
      response: "We deliver complete FF&E packages on one PO:\n\n• Casegoods: nightstands, desks, wardrobes, TV consoles, minibars\n• Soft seating: sofas, armchairs, headboards, banquettes\n• Lobby furniture: reception desks, lounge sets, dining furniture\n• Lighting: chandeliers, wall sconces, table lamps, floor lamps\n• Mattresses: box springs, mattresses, bed frames\n• Drapery: curtains, sheers, tracks, hardware\n• Bath vanities: vanity cabinets, mirrors, countertops\n• Hard surfaces (via partner network): stone, glass, aluminum doors/windows, curtain walls, hardware, bath fixtures\n\nEverything ships as one consolidated container from Foshan."
    },
    leadtime: {
      keywords: ['how long', 'lead time', 'delivery time', 'timeline', 'when', 'schedule', 'how many days', 'production time'],
      response: "Standard timeline:\n\n• Sampling: 30 days after drawing approval\n• Mass production: 48-60 days after sample confirmation\n• Sea freight: 25-35 days to Middle East / 30-40 days to North America\n• Total from order to site delivery: approximately 90-120 days\n\nRush orders can be discussed case by case."
    },
    warranty: {
      keywords: ['warranty', 'guarantee', 'defect', 'quality guarantee'],
      response: "We provide a 2-year warranty covering manufacturing defects. The warranty does not cover damage from improper installation, misuse, or normal wear and tear. Replacement parts are shipped within 15 days of claim approval."
    },
    certification: {
      keywords: ['certification', 'certified', 'UL', 'CARB', 'BS 7177', 'ISO', 'compliance', 'standard'],
      response: "We hold the following certifications:\n\n• UL (Underwriters Laboratories) — fire safety for US market\n• CARB P2 (California Air Resources Board) — formaldehyde emission standard\n• BS 7177 — UK fire safety for mattresses and upholstery\n• UAE Civil Defence — fire safety for UAE projects\n• EN 16798-2 — European ventilation and indoor air quality\n• ISO 9001:2015 — quality management system"
    },
    moq: {
      keywords: ['MOQ', 'minimum order', 'minimum quantity', 'small order'],
      response: "We work on full hotel project basis — complete guestroom floors or public areas on a single PO. We do not sell individual items as a retailer. Minimum engagement is one full project package."
    },
    price: {
      keywords: ['price', 'cost', 'how much', 'pricing', 'rate', 'budget', 'expensive', 'cheap', 'quotation', 'quote'],
      response: "For a detailed quotation, we'll need:\n\n1. Furniture list with dimensions and quantities (PDF/Excel/drawings)\n2. Material preferences or brand spec book\n3. Project site address (for DDP calculation)\n4. Target delivery date\n\nPlease share these details via our contact form or email us at chencanming@coze.email. Our specialist will prepare a quotation within 5-7 working days."
    },
    sample: {
      keywords: ['sample', 'send sample', 'sample cost', 'mockup', 'prototype'],
      response: "We can arrange samples after initial discussion. Sample lead time is approximately 30 days. Sample costs depend on the items requested. Shipping is typically at the buyer's expense (freight collect). Please share your requirements via our contact form and our team will follow up with details."
    },
    location: {
      keywords: ['where', 'location', 'factory', 'based', 'address', 'office'],
      response: "We are based in Foshan, Guangdong, China — the heart of China's furniture manufacturing hub. Our network of 19 specialized factories is concentrated in the Foshan/Dongguan/Guangzhou region, enabling efficient coordination and consolidated shipping."
    },
    contact: {
      keywords: ['contact', 'email', 'phone', 'reach', 'talk to', 'speak with'],
      response: "You can reach us at:\n\n• Email: chencanming@coze.email\n• WhatsApp: +86 136 3010 1668\n• Website: foshanFFE.com\n• For urgent inquiries, please use our contact form on this website.\n\nOur team typically responds within 24 hours."
    },
    portfolio: {
      keywords: ['portfolio', 'projects', 'cases', 'case study', 'previous work', 'references', 'gallery'],
      response: "You can view our project portfolio on our Projects page. We've delivered complete FF&E packages for Marriott, Hilton, IHG, Accor, Radisson, Wyndham, Red Sea Global, and Azizi Developments across the Middle East, North America, and other regions. Visit foshanFFE.com/projects to see our work."
    }
  };

  // Escalation triggers — these always route to human
  var ESCALATION_KEYWORDS = ['complaint', 'problem', 'broken', 'wrong', 'defect', 'damaged', 'lawyer', 'legal', 'sue', 'refund', 'cancel order', 'contract', 'payment terms', 'LC', 'letter of credit', 'dispute'];

  // ===== Widget Configuration =====
  var CONFIG = {
    primaryColor: '#1e40af',
    primaryHover: '#1e3a8a',
    bgLight: '#f8fafc',
    textDark: '#1e293b',
    textMuted: '#64748b',
    borderRadius: '12px',
    businessEmail: 'chencanming@coze.email',
    businessName: 'Foshan FF&E Solutions',
    responseDelay: 600
  };

  // ===== State =====
  var state = {
    isOpen: false,
    messages: [],
    step: 'greeting', // greeting | chatting | lead_capture | ended
    leadData: { name: '', email: '', company: '', message: '' },
    leadField: 'name'
  };

  // ===== Create Styles =====
  function injectStyles() {
    var style = document.createElement('style');
    style.textContent = `
      /* Lumen Chat Widget */
      #lumen-fab {
        position: fixed; bottom: 24px; right: 24px; z-index: 99999;
        width: 60px; height: 60px; border-radius: 50%;
        background: ${CONFIG.primaryColor}; color: #fff;
        border: none; cursor: pointer;
        box-shadow: 0 4px 14px rgba(30,64,175,0.35);
        display: flex; align-items: center; justify-content: center;
        transition: transform 0.2s, box-shadow 0.2s;
      }
      #lumen-fab:hover { transform: scale(1.08); box-shadow: 0 6px 20px rgba(30,64,175,0.45); }
      #lumen-fab svg { width: 28px; height: 28px; }
      #lumen-fab .lumen-badge {
        position: absolute; top: -2px; right: -2px;
        width: 18px; height: 18px; border-radius: 50%;
        background: #ef4444; color: #fff; font-size: 11px; font-weight: 700;
        display: flex; align-items: center; justify-content: center;
        border: 2px solid #fff;
      }
      #lumen-chat-window {
        position: fixed; bottom: 96px; right: 24px; z-index: 99999;
        width: 380px; max-width: calc(100vw - 32px);
        height: 520px; max-height: calc(100vh - 120px);
        background: #fff; border-radius: ${CONFIG.borderRadius};
        box-shadow: 0 12px 40px rgba(0,0,0,0.15);
        display: none; flex-direction: column; overflow: hidden;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }
      #lumen-chat-window.open { display: flex; }
      .lumen-header {
        background: ${CONFIG.primaryColor}; color: #fff;
        padding: 16px 20px; display: flex; align-items: center; gap: 12px;
        flex-shrink: 0;
      }
      .lumen-header-avatar {
        width: 36px; height: 36px; border-radius: 50%;
        background: rgba(255,255,255,0.2); display: flex;
        align-items: center; justify-content: center; font-weight: 700; font-size: 16px;
      }
      .lumen-header-info h4 { margin: 0; font-size: 15px; font-weight: 600; }
      .lumen-header-info span { font-size: 12px; opacity: 0.85; }
      .lumen-header-close {
        margin-left: auto; background: none; border: none; color: #fff;
        cursor: pointer; font-size: 20px; padding: 4px; opacity: 0.8;
      }
      .lumen-header-close:hover { opacity: 1; }
      .lumen-messages {
        flex: 1; overflow-y: auto; padding: 16px;
        display: flex; flex-direction: column; gap: 12px;
        background: ${CONFIG.bgLight};
      }
      .lumen-msg {
        max-width: 82%; padding: 10px 14px; border-radius: 16px;
        font-size: 14px; line-height: 1.5; word-wrap: break-word;
        white-space: pre-wrap;
      }
      .lumen-msg.bot {
        align-self: flex-start; background: #fff;
        border: 1px solid #e2e8f0; color: ${CONFIG.textDark};
        border-bottom-left-radius: 4px;
      }
      .lumen-msg.user {
        align-self: flex-end; background: ${CONFIG.primaryColor};
        color: #fff; border-bottom-right-radius: 4px;
      }
      .lumen-typing {
        align-self: flex-start; padding: 10px 14px;
        background: #fff; border: 1px solid #e2e8f0;
        border-radius: 16px; border-bottom-left-radius: 4px;
        display: flex; gap: 4px;
      }
      .lumen-typing span {
        width: 7px; height: 7px; border-radius: 50%;
        background: ${CONFIG.textMuted};
        animation: lumen-bounce 1.4s infinite ease-in-out;
      }
      .lumen-typing span:nth-child(2) { animation-delay: 0.16s; }
      .lumen-typing span:nth-child(3) { animation-delay: 0.32s; }
      @keyframes lumen-bounce {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
        40% { transform: scale(1); opacity: 1; }
      }
      .lumen-input-area {
        padding: 12px 16px; border-top: 1px solid #e2e8f0;
        display: flex; gap: 8px; flex-shrink: 0; background: #fff;
      }
      .lumen-input-area input {
        flex: 1; padding: 10px 14px; border: 1px solid #d1d5db;
        border-radius: 24px; font-size: 14px; outline: none;
        transition: border-color 0.2s;
      }
      .lumen-input-area input:focus { border-color: ${CONFIG.primaryColor}; }
      .lumen-input-area button {
        width: 40px; height: 40px; border-radius: 50%;
        background: ${CONFIG.primaryColor}; color: #fff;
        border: none; cursor: pointer; display: flex;
        align-items: center; justify-content: center;
        transition: background 0.2s;
      }
      .lumen-input-area button:hover { background: ${CONFIG.primaryHover}; }
      .lumen-input-area button svg { width: 18px; height: 18px; }
      .lumen-quick-replies {
        display: flex; flex-wrap: wrap; gap: 6px; padding: 0 16px 12px;
      }
      .lumen-quick-reply {
        padding: 6px 12px; border-radius: 16px; font-size: 13px;
        border: 1px solid ${CONFIG.primaryColor}; color: ${CONFIG.primaryColor};
        background: #fff; cursor: pointer; transition: all 0.2s;
      }
      .lumen-quick-reply:hover {
        background: ${CONFIG.primaryColor}; color: #fff;
      }
      @media (max-width: 480px) {
        #lumen-chat-window {
          bottom: 0; right: 0; left: 0;
          width: 100%; max-width: 100%; max-height: 100vh;
          border-radius: 0; height: 100vh;
        }
        #lumen-fab { bottom: 16px; right: 16px; }
      }
    `;
    document.head.appendChild(style);
  }

  // ===== Create DOM =====
  function createWidget() {
    // FAB Button
    var fab = document.createElement('button');
    fab.id = 'lumen-fab';
    fab.setAttribute('aria-label', 'Chat with us');
    fab.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg><span class="lumen-badge">1</span>';

    // Chat Window
    var win = document.createElement('div');
    win.id = 'lumen-chat-window';
    win.innerHTML = `
      <div class="lumen-header">
        <div class="lumen-header-avatar">L</div>
        <div class="lumen-header-info">
          <h4>Lumen</h4>
          <span>FF&E Specialist · Online</span>
        </div>
        <button class="lumen-header-close" id="lumen-close">&times;</button>
      </div>
      <div class="lumen-messages" id="lumen-messages"></div>
      <div class="lumen-quick-replies" id="lumen-quick-replies"></div>
      <div class="lumen-input-area">
        <input type="text" id="lumen-input" placeholder="Type your message..." autocomplete="off">
        <button id="lumen-send" aria-label="Send">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
        </button>
      </div>
    `;

    document.body.appendChild(fab);
    document.body.appendChild(win);

    // Events
    fab.addEventListener('click', toggleChat);
    document.getElementById('lumen-close').addEventListener('click', toggleChat);
    document.getElementById('lumen-send').addEventListener('click', handleSend);
    document.getElementById('lumen-input').addEventListener('keydown', function(e) {
      if (e.key === 'Enter') handleSend();
    });
  }

  // ===== Toggle Chat =====
  function toggleChat() {
    state.isOpen = !state.isOpen;
    var win = document.getElementById('lumen-chat-window');
    var fab = document.getElementById('lumen-fab');
    if (state.isOpen) {
      win.classList.add('open');
      fab.querySelector('.lumen-badge').style.display = 'none';
      if (state.messages.length === 0) {
        showGreeting();
      }
    } else {
      win.classList.remove('open');
    }
  }

  // ===== Show Typing =====
  function showTyping() {
    var msgs = document.getElementById('lumen-messages');
    var typing = document.createElement('div');
    typing.className = 'lumen-typing';
    typing.id = 'lumen-typing';
    typing.innerHTML = '<span></span><span></span><span></span>';
    msgs.appendChild(typing);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function hideTyping() {
    var typing = document.getElementById('lumen-typing');
    if (typing) typing.remove();
  }

  // ===== Add Message =====
  function addMessage(text, type) {
    var msgs = document.getElementById('lumen-messages');
    var div = document.createElement('div');
    div.className = 'lumen-msg ' + type;
    div.textContent = text;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    state.messages.push({ text: text, type: type });
  }

  // ===== Show Quick Replies =====
  function showQuickReplies(replies) {
    var container = document.getElementById('lumen-quick-replies');
    container.innerHTML = '';
    replies.forEach(function(r) {
      var btn = document.createElement('button');
      btn.className = 'lumen-quick-reply';
      btn.textContent = r;
      btn.addEventListener('click', function() {
        container.innerHTML = '';
        addMessage(r, 'user');
        processInput(r);
      });
      container.appendChild(btn);
    });
  }

  // ===== Greeting =====
  function showGreeting() {
    showTyping();
    setTimeout(function() {
      hideTyping();
      addMessage("Hi! Welcome to Foshan FF&E Solutions. I'm Lumen, your FF&E specialist assistant. How can I help you today?", 'bot');
      showQuickReplies(['About your company', 'Services & products', 'Lead time', 'Get a quote', 'Certifications']);
    }, CONFIG.responseDelay);
  }

  // ===== Match Knowledge Base =====
  function matchKB(input) {
    var lower = input.toLowerCase();

    // Check escalation first
    for (var i = 0; i < ESCALATION_KEYWORDS.length; i++) {
      if (lower.indexOf(ESCALATION_KEYWORDS[i]) !== -1) {
        return { type: 'escalation', text: null };
      }
    }

    // Match KB entries
    var keys = Object.keys(KB);
    for (var j = 0; j < keys.length; j++) {
      var entry = KB[keys[j]];
      for (var k = 0; k < entry.keywords.length; k++) {
        if (lower.indexOf(entry.keywords[k]) !== -1) {
          return { type: 'kb', text: entry.response };
        }
      }
    }

    return { type: 'unknown', text: null };
  }

  // ===== Process Input =====
  function processInput(input) {
    if (state.step === 'lead_capture') {
      handleLeadCapture(input);
      return;
    }

    var result = matchKB(input);

    if (result.type === 'escalation') {
      showTyping();
      setTimeout(function() {
        hideTyping();
        addMessage("Thank you for sharing that. This requires attention from our project specialist. Please share your name, email, and a brief description of your project, and we'll get back to you within 24 hours.", 'bot');
        state.step = 'lead_capture';
        state.leadField = 'name';
        showTyping();
        setTimeout(function() {
          hideTyping();
          addMessage("What's your name?", 'bot');
        }, CONFIG.responseDelay);
      }, CONFIG.responseDelay);
    } else if (result.type === 'kb') {
      showTyping();
      setTimeout(function() {
        hideTyping();
        addMessage(result.text, 'bot');
        // After KB response, offer next actions
        setTimeout(function() {
          showQuickReplies(['Get a quote', 'Contact us', 'Something else']);
        }, 300);
      }, CONFIG.responseDelay);
    } else {
      // Unknown — try to be helpful, then offer human handoff
      showTyping();
      setTimeout(function() {
        hideTyping();
        addMessage("Thanks for your message. To make sure you get the best answer, could you tell me more about what you're looking for? Are you interested in our services, need a quotation, or have a specific project in mind?", 'bot');
        showQuickReplies(['Get a quote', 'About your company', 'Services & products', 'Talk to a specialist']);
      }, CONFIG.responseDelay);
    }
  }

  // ===== Handle Send =====
  function handleSend() {
    var input = document.getElementById('lumen-input');
    var text = input.value.trim();
    if (!text) return;
    input.value = '';
    addMessage(text, 'user');
    processInput(text);
  }

  // ===== Lead Capture Flow =====
  function handleLeadCapture(input) {
    var field = state.leadField;
    state.leadData[field] = input;

    var fields = ['name', 'email', 'company', 'message'];
    var nextIndex = fields.indexOf(field) + 1;

    if (nextIndex < fields.length) {
      state.leadField = fields[nextIndex];
      var prompts = {
        email: "Great! What's your email address?",
        company: "Thanks! What's your company name?",
        message: "Almost done! Briefly describe your project (hotel brand, number of rooms, location, timeline):"
      };
      showTyping();
      setTimeout(function() {
        hideTyping();
        addMessage(prompts[state.leadField], 'bot');
      }, CONFIG.responseDelay);
    } else {
      // Lead capture complete — send to email
      showTyping();
      setTimeout(function() {
        hideTyping();
        addMessage("Thank you, " + state.leadData.name + "! Your inquiry has been received. Our project specialist will review your details and get back to you within 24 hours at " + state.leadData.email + ".\n\nFor urgent matters, you can also reach us directly at " + CONFIG.businessEmail + ".", 'bot');
        // Compose mailto link for lead data
        var subject = encodeURIComponent('Website Inquiry: ' + state.leadData.company);
        var body = encodeURIComponent(
          'New website inquiry from Lumen chat:\n\n' +
          'Name: ' + state.leadData.name + '\n' +
          'Email: ' + state.leadData.email + '\n' +
          'Company: ' + state.leadData.company + '\n' +
          'Project: ' + state.leadData.message + '\n' +
          'Source: foshanFFE.com chat widget'
        );
        // Open mailto in background
        var mailLink = document.createElement('a');
        mailLink.href = 'mailto:' + CONFIG.businessEmail + '?subject=' + subject + '&body=' + body;
        mailLink.style.display = 'none';
        document.body.appendChild(mailLink);
        mailLink.click();
        document.body.removeChild(mailLink);
        state.step = 'ended';
      }, CONFIG.responseDelay);
    }
  }

  // ===== Initialize =====
  function init() {
    injectStyles();
    createWidget();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
