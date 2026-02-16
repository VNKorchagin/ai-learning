/**
 * AI-Объяснялка - Frontend JavaScript
 */

// ===== State =====
const state = {
    currentLevel: 'child',
    isLoading: false,
    history: JSON.parse(localStorage.getItem('ai_explainer_history') || '[]'),
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
};

// ===== Event Listeners =====
document.addEventListener('DOMContentLoaded', () => {
    initLevelButtons();
    initExplainButton();
    initEnterKey();
    renderHistory();
});

// ===== Initialization =====
function initLevelButtons() {
    const buttons = elements.levelsContainer.querySelectorAll('.level-btn');
    
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active from all
            buttons.forEach(b => b.classList.remove('active'));
            // Add active to clicked
            btn.classList.add('active');
            // Update state
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
    
    // Set loading state
    setLoading(true);
    
    try {
        console.log('🚀 Отправка запроса:', { topic, level: state.currentLevel });
        
        const response = await fetch('/api/explain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                topic: topic,
                level: state.currentLevel,
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
    
    if (loading) {
        elements.explanationText.classList.add('loading');
    } else {
        elements.explanationText.classList.remove('loading');
    }
}

function showError(message) {
    elements.errorMessage.textContent = `⚠️ ${message}`;
    elements.errorMessage.classList.remove('hidden');
    
    // Auto-hide after 5 seconds
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
