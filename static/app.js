/**
 * AI-Объяснялка - Frontend JavaScript
 */

// ===== State =====
const state = {
    currentLevel: 'child',
    isLoading: false,
    history: JSON.parse(localStorage.getItem('ai_explainer_history') || '[]'),
    settings: JSON.parse(localStorage.getItem('ai_explainer_settings') || '{}'),
    isSettingsOpen: false,
};

// ===== Default Settings =====
const defaultSettings = {
    formatDescription: '',
    maxTokens: 2000,
    stopSequence: '',
    explicitStop: true,
};

// ===== DOM Elements =====
const elements = {
    topicInput: document.getElementById('topic-input'),
    explainBtn: document.getElementById('explain-btn'),
    btnText: document.querySelector('.btn-text'),
    btnLoader: document.querySelector('.btn-loader'),
    levelsContainer: document.getElementById('levels-container'),
    errorMessage: document.getElementById('error-message'),
    resultSection: document.getElementById('result-section'),
    resultTopic: document.getElementById('result-topic'),
    resultLevel: document.getElementById('result-level'),
    explanationText: document.getElementById('explanation-text'),
    usageInfo: document.getElementById('usage-info'),
    tokensPrompt: document.getElementById('tokens-prompt'),
    tokensCompletion: document.getElementById('tokens-completion'),
    tokensTotal: document.getElementById('tokens-total'),
    modelUsed: document.getElementById('model-used'),
    historySection: document.getElementById('history-section'),
    historyList: document.getElementById('history-list'),
    // Settings elements
    settingsBtn: document.getElementById('settings-btn'),
    settingsPanel: document.getElementById('settings-panel'),
    closeSettings: document.getElementById('close-settings'),
    formatDescription: document.getElementById('format-description'),
    maxTokens: document.getElementById('max-tokens'),
    maxTokensValue: document.getElementById('max-tokens-value'),
    stopSequence: document.getElementById('stop-sequence'),
    explicitStop: document.getElementById('explicit-stop'),
    resetSettings: document.getElementById('reset-settings'),
    applySettings: document.getElementById('apply-settings'),
};

// ===== Event Listeners =====
document.addEventListener('DOMContentLoaded', () => {
    initLevelButtons();
    initExplainButton();
    initEnterKey();
    initSettings();
    loadSettings();
    renderHistory();
});

// ===== Initialization =====
function initLevelButtons() {
    const buttons = elements.levelsContainer.querySelectorAll('.level-btn');
    
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.currentLevel = btn.dataset.level;
        });
    });
}

function initExplainButton() {
    elements.explainBtn.addEventListener('click', handleExplain);
}

function initEnterKey() {
    elements.topicInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !state.isLoading) {
            handleExplain();
        }
    });
}

// ===== Settings Functions =====
function initSettings() {
    // Toggle settings panel
    elements.settingsBtn.addEventListener('click', toggleSettings);
    elements.closeSettings.addEventListener('click', toggleSettings);
    
    // Update range value display
    elements.maxTokens.addEventListener('input', (e) => {
        elements.maxTokensValue.textContent = e.target.value;
    });
    
    // Apply and reset buttons
    elements.applySettings.addEventListener('click', saveSettingsToStorage);
    elements.resetSettings.addEventListener('click', resetSettings);
    
    // Close settings when clicking outside
    document.addEventListener('click', (e) => {
        if (state.isSettingsOpen && 
            !elements.settingsPanel.contains(e.target) && 
            !elements.settingsBtn.contains(e.target)) {
            toggleSettings();
        }
    });
}

function toggleSettings() {
    state.isSettingsOpen = !state.isSettingsOpen;
    elements.settingsPanel.classList.toggle('hidden', !state.isSettingsOpen);
    elements.settingsBtn.classList.toggle('active', state.isSettingsOpen);
}

function loadSettings() {
    const settings = { ...defaultSettings, ...state.settings };
    
    elements.formatDescription.value = settings.formatDescription || '';
    elements.maxTokens.value = settings.maxTokens || 2000;
    elements.maxTokensValue.textContent = settings.maxTokens || 2000;
    elements.stopSequence.value = settings.stopSequence || '';
    elements.explicitStop.checked = settings.explicitStop !== false;
}

function saveSettingsToStorage() {
    const settings = {
        formatDescription: elements.formatDescription.value.trim(),
        maxTokens: parseInt(elements.maxTokens.value),
        stopSequence: elements.stopSequence.value.trim(),
        explicitStop: elements.explicitStop.checked,
    };
    
    state.settings = settings;
    localStorage.setItem('ai_explainer_settings', JSON.stringify(settings));
    
    // Visual feedback
    elements.applySettings.textContent = '✓ Сохранено!';
    elements.applySettings.style.background = 'linear-gradient(135deg, #00d9ff, #00b4d8)';
    
    setTimeout(() => {
        elements.applySettings.textContent = '✓ Применить';
        elements.applySettings.style.background = '';
        toggleSettings();
    }, 800);
}

function resetSettings() {
    elements.formatDescription.value = '';
    elements.maxTokens.value = 2000;
    elements.maxTokensValue.textContent = 2000;
    elements.stopSequence.value = '';
    elements.explicitStop.checked = true;
    
    state.settings = { ...defaultSettings };
    localStorage.setItem('ai_explainer_settings', JSON.stringify(state.settings));
}

function getSettings() {
    return {
        formatDescription: elements.formatDescription.value.trim(),
        maxTokens: parseInt(elements.maxTokens.value),
        stopSequence: elements.stopSequence.value.trim(),
        explicitStop: elements.explicitStop.checked,
    };
}

// ===== Main Function =====
async function handleExplain() {
    const topic = elements.topicInput.value.trim();
    
    // Validation
    if (!topic) {
        showError('Введите тему для объяснения');
        elements.topicInput.focus();
        return;
    }
    
    if (topic.length < 2) {
        showError('Тема слишком короткая');
        return;
    }
    
    // Clear previous errors
    hideError();
    
    // Close settings if open
    if (state.isSettingsOpen) {
        toggleSettings();
    }
    
    // Set loading state
    setLoading(true);
    
    // Get settings
    const settings = getSettings();
    
    try {
        console.log('🚀 Отправка запроса:', { topic, level: state.currentLevel, settings });
        
        const response = await fetch('/api/explain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                topic: topic,
                level: state.currentLevel,
                format_description: settings.formatDescription,
                max_tokens: settings.maxTokens,
                stop_sequence: settings.stopSequence,
                explicit_stop: settings.explicitStop,
            }),
        });
        
        console.log('📡 HTTP Status:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Получен ответ:', data);
        
        // Display result
        displayResult(data);
        
        // Add to history
        addToHistory(data);
        
    } catch (error) {
        console.error('❌ Ошибка:', error);
        showError(error.message || 'Произошла ошибка при запросе к API');
    } finally {
        setLoading(false);
    }
}

// ===== Display Functions =====
function displayResult(data) {
    // Show result section
    elements.resultSection.classList.remove('hidden');
    
    // Set topic and level
    elements.resultTopic.textContent = data.topic;
    elements.resultLevel.textContent = data.level_name;
    
    // Animate text typing
    typeText(elements.explanationText, data.explanation);
    
    // Show usage info
    if (data.usage) {
        elements.usageInfo.classList.remove('hidden');
        elements.tokensPrompt.textContent = `📝 Prompt tokens: ${data.usage.prompt_tokens || 0}`;
        elements.tokensCompletion.textContent = `💬 Completion tokens: ${data.usage.completion_tokens || 0}`;
        elements.tokensTotal.textContent = `📊 Total tokens: ${data.usage.total_tokens || 0}`;
        elements.modelUsed.textContent = `🤖 Модель: ${data.model || 'unknown'}`;
    }
    
    // Show settings info if custom settings were used
    if (data.settings && (data.settings.format_description || data.settings.stop_sequence || data.settings.max_tokens !== 2000)) {
        const settingsInfo = document.createElement('div');
        settingsInfo.className = 'settings-used-info';
        settingsInfo.innerHTML = `
            <details>
                <summary>⚙️ Применённые настройки</summary>
                <div class="settings-details">
                    ${data.settings.format_description ? `<div>📝 Формат: ${escapeHtml(data.settings.format_description)}</div>` : ''}
                    ${data.settings.stop_sequence ? `<div>🛑 Стоп-слово: ${escapeHtml(data.settings.stop_sequence)}</div>` : ''}
                    <div>📏 Max tokens: ${data.settings.max_tokens}</div>
                    <div>⛔ Явная инструкция: ${data.settings.explicit_stop ? 'да' : 'нет'}</div>
                </div>
            </details>
        `;
        
        // Remove previous settings info if exists
        const prevSettings = elements.resultSection.querySelector('.settings-used-info');
        if (prevSettings) prevSettings.remove();
        
        elements.resultSection.insertBefore(settingsInfo, elements.usageInfo);
    }
    
    // Scroll to result
    elements.resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function typeText(element, text) {
    element.innerHTML = '';
    element.classList.add('typing-cursor');
    
    let index = 0;
    const speed = 5; // ms per character (fast typing)
    
    function type() {
        if (index < text.length) {
            element.textContent += text.charAt(index);
            index++;
            setTimeout(type, speed);
        } else {
            element.classList.remove('typing-cursor');
        }
    }
    
    type();
}

// ===== History Functions =====
function addToHistory(data) {
    const historyItem = {
        topic: data.topic,
        level: data.level,
        levelName: data.level_name,
        explanation: data.explanation,
        settings: data.settings,
        timestamp: new Date().toISOString(),
    };
    
    // Add to beginning
    state.history.unshift(historyItem);
    
    // Keep only last 10
    if (state.history.length > 10) {
        state.history = state.history.slice(0, 10);
    }
    
    // Save to localStorage
    localStorage.setItem('ai_explainer_history', JSON.stringify(state.history));
    
    // Re-render
    renderHistory();
}

function renderHistory() {
    if (state.history.length === 0) {
        elements.historySection.classList.add('hidden');
        return;
    }
    
    elements.historySection.classList.remove('hidden');
    
    elements.historyList.innerHTML = state.history.map((item, index) => `
        <div class="history-item" data-index="${index}">
            <span class="history-item-topic">${escapeHtml(item.topic)}</span>
            <span class="history-item-level">${item.levelName}</span>
        </div>
    `).join('');
    
    // Add click handlers
    elements.historyList.querySelectorAll('.history-item').forEach(el => {
        el.addEventListener('click', () => {
            const index = parseInt(el.dataset.index);
            loadFromHistory(index);
        });
    });
}

function loadFromHistory(index) {
    const item = state.history[index];
    if (!item) return;
    
    elements.topicInput.value = item.topic;
    state.currentLevel = item.level;
    
    // Update level buttons
    const buttons = elements.levelsContainer.querySelectorAll('.level-btn');
    buttons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.level === item.level);
    });
    
    // Load settings if present
    if (item.settings) {
        elements.formatDescription.value = item.settings.format_description || '';
        elements.maxTokens.value = item.settings.max_tokens || 2000;
        elements.maxTokensValue.textContent = item.settings.max_tokens || 2000;
        elements.stopSequence.value = item.settings.stop_sequence || '';
        elements.explicitStop.checked = item.settings.explicit_stop !== false;
    }
    
    // Display result directly without animation
    elements.resultSection.classList.remove('hidden');
    elements.resultTopic.textContent = item.topic;
    elements.resultLevel.textContent = item.levelName;
    elements.explanationText.textContent = item.explanation;
    elements.usageInfo.classList.add('hidden');
    
    elements.resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ===== Utility Functions =====
function setLoading(loading) {
    state.isLoading = loading;
    
    elements.explainBtn.disabled = loading;
    elements.btnText.classList.toggle('hidden', loading);
    elements.btnLoader.classList.toggle('hidden', !loading);
    elements.topicInput.disabled = loading;
    elements.settingsBtn.disabled = loading;
    
    if (loading) {
        elements.explanationText.classList.add('loading');
    } else {
        elements.explanationText.classList.remove('loading');
    }
}

function showError(message) {
    elements.errorMessage.textContent = `⚠️ ${message}`;
    elements.errorMessage.classList.remove('hidden');
    
    setTimeout(() => {
        hideError();
    }, 5000);
}

function hideError() {
    elements.errorMessage.classList.add('hidden');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
