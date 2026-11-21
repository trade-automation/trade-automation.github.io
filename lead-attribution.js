/* foshanFFE first-touch lead attribution. No PII is collected until a form is submitted. */
(function (window, document) {
  'use strict';

  var FIRST_TOUCH_KEY = 'ffe_first_touch_v1';
  var PENDING_PREFIX = 'ffe_lead_pending_v1_';
  var LOGGED_KEY = 'ffe_lead_logged_v1';
  var MAX_PENDING_AGE_MS = 2 * 60 * 60 * 1000;
  var ATTRIBUTION_FIELDS = [
    'first_landing_page', 'submission_page', 'referrer',
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'gclid', 'form_name', 'submission_id'
  ];
  var FIRST_TOUCH_FIELDS = [
    'first_landing_page', 'referrer', 'utm_source', 'utm_medium',
    'utm_campaign', 'utm_term', 'utm_content', 'gclid'
  ];

  function storage(kind) {
    try {
      var store = window[kind];
      var probe = '__ffe_probe__';
      store.setItem(probe, '1');
      store.removeItem(probe);
      return store;
    } catch (e) {
      return null;
    }
  }

  function readJSON(store, key, fallback) {
    if (!store) return fallback;
    try {
      var value = store.getItem(key);
      return value ? JSON.parse(value) : fallback;
    } catch (e) {
      return fallback;
    }
  }

  function writeJSON(store, key, value) {
    if (!store) return false;
    try {
      store.setItem(key, JSON.stringify(value));
      return true;
    } catch (e) {
      return false;
    }
  }

  function pagePath(location) {
    return (location.pathname || '/') + (location.search || '');
  }

  function sameOriginPath(url, location) {
    if (!url) return '';
    try {
      var parsed = new URL(url, location.href);
      if (parsed.origin !== location.origin) return '';
      return parsed.pathname + parsed.search;
    } catch (e) {
      return '';
    }
  }

  function captureFirstTouch() {
    var local = storage('localStorage');
    var existing = readJSON(local, FIRST_TOUCH_KEY, null);
    if (existing && existing.first_landing_page) return existing;

    var params = new URLSearchParams(window.location.search || '');
    var referrerPath = sameOriginPath(document.referrer || '', window.location);
    var first = {
      first_landing_page: referrerPath || pagePath(window.location),
      referrer: document.referrer || '',
      utm_source: params.get('utm_source') || '',
      utm_medium: params.get('utm_medium') || '',
      utm_campaign: params.get('utm_campaign') || '',
      utm_term: params.get('utm_term') || '',
      utm_content: params.get('utm_content') || '',
      gclid: params.get('gclid') || ''
    };
    writeJSON(local, FIRST_TOUCH_KEY, first);
    return first;
  }

  function makeSubmissionId() {
    if (window.crypto && typeof window.crypto.randomUUID === 'function') {
      return 'ffe_' + window.crypto.randomUUID();
    }
    if (window.crypto && typeof window.crypto.getRandomValues === 'function') {
      var bytes = new Uint8Array(16);
      window.crypto.getRandomValues(bytes);
      return 'ffe_' + Array.prototype.map.call(bytes, function (b) {
        return ('0' + b.toString(16)).slice(-2);
      }).join('');
    }
    return 'ffe_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2);
  }

  function createSubmission(formName) {
    var first = captureFirstTouch();
    var session = storage('sessionStorage');
    var data = {
      first_landing_page: first.first_landing_page || '',
      submission_page: pagePath(window.location),
      referrer: first.referrer || '',
      utm_source: first.utm_source || '',
      utm_medium: first.utm_medium || '',
      utm_campaign: first.utm_campaign || '',
      utm_term: first.utm_term || '',
      utm_content: first.utm_content || '',
      gclid: first.gclid || '',
      form_name: formName || 'website_inquiry',
      submission_id: makeSubmissionId(),
      created_at: Date.now()
    };
    writeJSON(session, PENDING_PREFIX + data.submission_id, data);
    return data;
  }

  function setHidden(form, name, value) {
    var field = form.querySelector('input[name="' + name + '"]');
    if (!field) {
      field = document.createElement('input');
      field.type = 'hidden';
      field.name = name;
      form.appendChild(field);
    }
    field.value = value == null ? '' : String(value);
  }

  function applyToForm(form, data) {
    ATTRIBUTION_FIELDS.forEach(function (name) {
      setHidden(form, name, data[name] || '');
    });
    var next = form.querySelector('input[name="_next"]');
    if (next && next.value) {
      var nextUrl = new URL(next.value, window.location.href);
      nextUrl.searchParams.set('submission_id', data.submission_id);
      next.value = nextUrl.href;
    }
    var subject = form.querySelector('input[name="_subject"]');
    if (subject && subject.value.indexOf(data.submission_id) === -1) {
      subject.value += ' [' + data.submission_id + ']';
    }
  }

  function bindForm(form) {
    if (!form || form.getAttribute('data-ffe-lead-bound') === 'true') return;
    form.setAttribute('data-ffe-lead-bound', 'true');
    form.addEventListener('submit', function (event) {
      if (event.defaultPrevented) return;
      if (form.getAttribute('data-ffe-lead-submitted') === 'true') {
        event.preventDefault();
        return;
      }
      var formName = form.getAttribute('data-ffe-lead-form') || 'website_inquiry';
      var data = createSubmission(formName);
      applyToForm(form, data);
      form.setAttribute('data-ffe-lead-submitted', 'true');
    });
  }

  function bindForms() {
    if (window.location.pathname === '/thank-you.html') return;
    captureFirstTouch();
    var forms = document.querySelectorAll('form[data-ffe-lead-form]');
    Array.prototype.forEach.call(forms, bindForm);
  }

  function consumeThankYou() {
    var session = storage('sessionStorage');
    var local = storage('localStorage');
    var id = new URLSearchParams(window.location.search || '').get('submission_id') || '';
    if (!/^ffe_[A-Za-z0-9_-]{8,80}$/.test(id)) return null;

    var logged = readJSON(local, LOGGED_KEY, []);
    if (!Array.isArray(logged)) logged = [];
    if (logged.indexOf(id) !== -1) return null;

    var pending = readJSON(session, PENDING_PREFIX + id, null);
    if (!pending || pending.submission_id !== id || !pending.form_name) return null;
    if (!pending.created_at || Date.now() - pending.created_at > MAX_PENDING_AGE_MS) {
      if (session) session.removeItem(PENDING_PREFIX + id);
      return null;
    }

    /* Consume before emitting so refresh, back/forward and duplicate tabs cannot recount it. */
    if (session) session.removeItem(PENDING_PREFIX + id);
    logged.push(id);
    writeJSON(local, LOGGED_KEY, logged.slice(-50));

    var eventData = {};
    ATTRIBUTION_FIELDS.forEach(function (name) {
      if (pending[name]) eventData[name] = pending[name];
    });
    return eventData;
  }

  window.ffeLeadAttribution = {
    fields: ATTRIBUTION_FIELDS.slice(),
    captureFirstTouch: captureFirstTouch,
    createSubmission: createSubmission,
    applyToForm: applyToForm,
    bindForm: bindForm,
    consumeThankYou: consumeThankYou
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bindForms);
  } else {
    bindForms();
  }
})(window, document);
