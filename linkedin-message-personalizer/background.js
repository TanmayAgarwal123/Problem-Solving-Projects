// background.js - Enhanced background script with better LinkedIn integration

console.log("LinkedIn Message Personalizer background script loaded");

// Listen for installation
chrome.runtime.onInstalled.addListener(function(details) {
  console.log("Extension installed/updated:", details.reason);
  
  if (details.reason === 'install') {
    // First time installation
    console.log("First time installation detected");
    
    // Initialize with default templates
    initializeDefaultTemplates();
    
    // Set initial settings
    chrome.storage.sync.set({
      extensionSettings: {
        debugMode: false,
        autoGenerate: true,
        showNotifications: true,
        version: chrome.runtime.getManifest().version
      }
    });
    
    // Open welcome page (optional)
    // chrome.tabs.create({ url: 'welcome.html' });
  } else if (details.reason === 'update') {
    console.log("Extension updated to version:", chrome.runtime.getManifest().version);
    // Handle updates if needed
  }
});

// Initialize default templates
function initializeDefaultTemplates() {
  chrome.storage.sync.get('templates', function(data) {
    if (!data.templates || data.templates.length === 0) {
      const defaultTemplates = [
        {
          name: "Basic Connection",
          content: "Hi {firstName}, I came across your profile and was impressed by your work at {company}. I'd love to connect and potentially collaborate in the future.",
          category: "general",
          created: new Date().toISOString()
        },
        {
          name: "Industry Specific",
          content: "Hello {firstName}, Your experience in {industry} at {company} really caught my attention. I'm working on similar projects and would value the opportunity to connect and share insights.",
          category: "industry",
          created: new Date().toISOString()
        },
        {
          name: "Skill-Based",
          content: "Hi {firstName}, I noticed we both have experience with {skill}. I've been following developments in this area and would love to connect with someone who shares this expertise at {company}.",
          category: "skills",
          created: new Date().toISOString()
        },
        {
          name: "Learning Focused",
          content: "Hello {firstName}, I'm really impressed by your {experience} background in {skill}. I'm always looking to learn from experienced professionals like yourself. Would you be open to connecting?",
          category: "learning",
          created: new Date().toISOString()
        },
        {
          name: "Mutual Interest",
          content: "Hi {firstName}, I see we're both passionate about {industry} and innovation. Your work at {company} aligns well with my professional interests. I'd love to expand my network with like-minded professionals.",
          category: "interest",
          created: new Date().toISOString()
        }
      ];
      
      chrome.storage.sync.set({templates: defaultTemplates}, function() {
        console.log("Default templates initialized:", defaultTemplates.length);
      });
    }
  });
}

// Listen for tab updates to enable/disable the extension icon
chrome.tabs.onUpdated.addListener(function(tabId, changeInfo, tab) {
  if (changeInfo.status === 'complete' && tab.url) {
    handleTabUpdate(tabId, tab);
  }
});

// Listen for tab activation
chrome.tabs.onActivated.addListener(function(activeInfo) {
  chrome.tabs.get(activeInfo.tabId, function(tab) {
    if (tab.url) {
      handleTabUpdate(activeInfo.tabId, tab);
    }
  });
});

function handleTabUpdate(tabId, tab) {
  const url = tab.url.toLowerCase();
  
  if (url.includes('linkedin.com')) {
    // We're on LinkedIn
    chrome.action.enable(tabId);
    
    if (url.includes('/in/') && !url.includes('linkedin.com/in/unavailable')) {
      // We're on a profile page
      console.log("LinkedIn profile detected:", tab.url);
      
      // Update badge to show we're ready
      chrome.action.setBadgeText({
        text: '✓',
        tabId: tabId
      });
      
      chrome.action.setBadgeBackgroundColor({
        color: '#28a745',
        tabId: tabId
      });
      
      // Inject content script if needed (fallback)
      chrome.scripting.executeScript({
        target: { tabId: tabId },
        files: ['ai-processor.js', 'content.js']
      }).catch(error => {
        console.log("Content script already injected or injection failed:", error);
      });
    } else {
      // On LinkedIn but not a profile page
      chrome.action.setBadgeText({
        text: '',
        tabId: tabId
      });
    }
  } else {
    // Not on LinkedIn
    chrome.action.disable(tabId);
    chrome.action.setBadgeText({
      text: '',
      tabId: tabId
    });
  }
}

// Handle messages from content scripts or popup
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  console.log("Background received message:", request);
  
  switch (request.action) {
    case 'getExtensionSettings':
      chrome.storage.sync.get('extensionSettings', function(data) {
        sendResponse(data.extensionSettings || {});
      });
      return true;
      
    case 'updateExtensionSettings':
      chrome.storage.sync.set({
        extensionSettings: request.settings
      }, function() {
        console.log("Extension settings updated:", request.settings);
        sendResponse({success: true});
      });
      return true;
      
    case 'logAnalytics':
      // You could implement analytics logging here
      console.log("Analytics event:", request.event, request.data);
      sendResponse({success: true});
      return true;
      
    case 'showNotification':
      if (request.message) {
        chrome.notifications.create({
          type: 'basic',
          iconUrl: 'images/icon48.png',
          title: 'LinkedIn Message Personalizer',
          message: request.message
        });
      }
      sendResponse({success: true});
      return true;
      
    default:
      console.log("Unknown action:", request.action);
      sendResponse({error: 'Unknown action'});
      return false;
  }
});

// Handle extension icon click (when popup doesn't open)
chrome.action.onClicked.addListener(function(tab) {
  console.log("Extension icon clicked on tab:", tab.url);
  
  if (!tab.url.includes('linkedin.com')) {
    // Redirect to LinkedIn if not already there
    chrome.tabs.update(tab.id, {
      url: 'https://linkedin.com'
    });
  }
});

// Clean up old data periodically
chrome.alarms.create('cleanup', {
  delayInMinutes: 1,
  periodInMinutes: 60 * 24 // Once per day
});

chrome.alarms.onAlarm.addListener(function(alarm) {
  if (alarm.name === 'cleanup') {
    cleanupOldData();
  }
});

function cleanupOldData() {
  // Clean up old analytics data, temporary data, etc.
  chrome.storage.local.get(null, function(items) {
    const keysToRemove = [];
    const now = Date.now();
    const oneWeekAgo = now - (7 * 24 * 60 * 60 * 1000);
    
    for (const [key, value] of Object.entries(items)) {
      if (key.startsWith('temp_') || key.startsWith('cache_')) {
        if (value.timestamp && value.timestamp < oneWeekAgo) {
          keysToRemove.push(key);
        }
      }
    }
    
    if (keysToRemove.length > 0) {
      chrome.storage.local.remove(keysToRemove, function() {
        console.log("Cleaned up", keysToRemove.length, "old data entries");
      });
    }
  });
}

// Error handling
chrome.runtime.onSuspend.addListener(function() {
  console.log("Extension suspending...");
});

// Handle startup
chrome.runtime.onStartup.addListener(function() {
  console.log("Extension starting up...");
});