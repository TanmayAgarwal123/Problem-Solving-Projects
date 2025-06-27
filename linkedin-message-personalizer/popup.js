// Debug mode for development
let isDebugMode = true; // Set to true for debugging

document.addEventListener('DOMContentLoaded', function() {
  // Store profile data and insights
  let currentProfileData = null;
  let currentProfileInsights = null;
  
  if (isDebugMode) {
    console.log("Popup loaded, initializing...");
  }
  
  // Load saved templates
  loadTemplates();
  
  // Check if we're on a LinkedIn profile page
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    if (isDebugMode) {
      console.log("Querying current tab:", tabs[0].url);
    }
    
    // Check if we're on LinkedIn
    if (!tabs[0].url.includes('linkedin.com')) {
      document.getElementById('profile-details').innerHTML = `
        <p class="warning">Please navigate to a LinkedIn profile page to use this extension.</p>
      `;
      return;
    }
    
    chrome.tabs.sendMessage(tabs[0].id, {action: "getProfileData"}, function(response) {
      if (isDebugMode) {
        console.log("Response from content script:", response);
      }
      
      if (chrome.runtime.lastError) {
        console.log("Error communicating with content script:", chrome.runtime.lastError);
        showDemoMode();
        return;
      }
      
      if (response && response.profileData) {
        currentProfileData = response.profileData;
        currentProfileInsights = response.profileInsights;
        
        displayProfileData(response.profileData);
        if (response.profileInsights) {
          displayProfileInsights(response.profileInsights);
        }
      } else {
        // Handle case where we couldn't get profile data
        showDemoMode();
      }
    });
  });
  
  // Event listeners
  document.getElementById('generate-message').addEventListener('click', function() {
    if (currentProfileData && currentProfileInsights) {
      generatePersonalizedMessage(currentProfileData, currentProfileInsights);
    } else {
      useDemoData();
    }
  });
  
  document.getElementById('copy-message').addEventListener('click', copyMessageToClipboard);
  document.getElementById('create-template').addEventListener('click', showTemplateCreator);
  
  // Add template selection change listener
  document.getElementById('template-select').addEventListener('change', function() {
    if (this.value !== '') {
      if (currentProfileData && currentProfileInsights) {
        generatePersonalizedMessage(currentProfileData, currentProfileInsights);
      } else {
        useDemoData();
      }
    }
  });
  
  // Add test mode button in debug mode
  if (isDebugMode) {
    addTestButton();
  }
});

function showDemoMode() {
  document.getElementById('profile-details').innerHTML = `
    <p class="info">Could not extract profile data from this page.</p>
    <p>This might happen if:</p>
    <ul style="margin: 10px 0; padding-left: 20px; font-size: 12px;">
      <li>You're not on a LinkedIn profile page</li>
      <li>LinkedIn has changed their page structure</li>
      <li>The profile has privacy restrictions</li>
    </ul>
    <p class="info">Click "Test Mode" to see how the extension works with demo data.</p>
  `;
}

// Add test button for demo mode
function addTestButton() {
  const actionsDiv = document.querySelector('.actions');
  if (actionsDiv && !document.getElementById('test-button')) {
    const testButton = document.createElement('button');
    testButton.id = 'test-button';
    testButton.textContent = 'Test Mode';
    testButton.style.backgroundColor = '#f0ad4e';
    testButton.style.marginLeft = '5px';
    actionsDiv.appendChild(testButton);
    
    testButton.addEventListener('click', useDemoData);
  }
}

// Demo data function for testing
function useDemoData() {
  if (isDebugMode) {
    console.log("Using demo data for development/testing");
  }
  
  const demoProfileData = {
    name: "Alex Johnson",
    title: "Senior Software Engineer at TechCorp",
    company: "TechCorp",
    industry: "Technology",
    education: "University of California, Berkeley",
    skills: ["JavaScript", "React", "Node.js", "Machine Learning", "Python"],
    about: "Passionate software engineer with 8+ years of experience building scalable web applications. I love working with modern technologies and am always excited to tackle challenging problems. Currently focused on machine learning integration in web applications.",
    mutualConnections: ["Sarah Chen", "Mike Rodriguez"]
  };
  
  // Create demo insights using our AI processor
  if (window.AIProcessor) {
    const aiProcessor = new AIProcessor();
    currentProfileInsights = aiProcessor.analyzeProfile(demoProfileData);
  } else {
    // Fallback if AI processor not available
    currentProfileInsights = {
      careerLevel: 'senior',
      industryFocus: 'technology',
      keySkills: ['JavaScript', 'React', 'Machine Learning'],
      connectionStrategy: 'technical_collaboration',
      communicationStyle: 'balanced'
    };
  }
  
  currentProfileData = demoProfileData;
  
  displayProfileData(demoProfileData);
  displayProfileInsights(currentProfileInsights);
  
  // Auto-generate a message if a template is selected
  const templateSelect = document.getElementById('template-select');
  if (templateSelect.value !== '') {
    generatePersonalizedMessage(demoProfileData, currentProfileInsights);
  }
}

function loadTemplates() {
  chrome.storage.sync.get('templates', function(data) {
    const templateSelect = document.getElementById('template-select');
    
    // Clear existing options except the first one
    while (templateSelect.options.length > 1) {
      templateSelect.remove(1);
    }
    
    if (data.templates && data.templates.length > 0) {
      data.templates.forEach(function(template, index) {
        const option = document.createElement('option');
        option.value = index;
        option.textContent = template.name;
        templateSelect.appendChild(option);
      });
    } else {
      // Add default templates if none exist
      const defaultTemplates = [
        {
          name: "Basic Connection",
          content: "Hi {firstName}, I noticed your profile while browsing LinkedIn and I'm impressed with your experience in {industry}. I'd love to connect and learn more about your work at {company}."
        },
        {
          name: "Mutual Connection",
          content: "Hi {firstName}, I see we're both connected with {mutualConnection}. I've been working in {industry} for some time now, and I'd love to expand my network with professionals like you who are doing great work at {company}."
        },
        {
          name: "Skill-Based",
          content: "Hi {firstName}, I came across your profile and was particularly impressed by your expertise in {skill}. As someone who also works with {skill}, I'd love to connect and exchange insights about the latest trends in our field."
        },
        {
          name: "Industry Focus",
          content: "Hi {firstName}, I noticed you're working in {industry} at {company}. I'm passionate about {industry} innovations and would love to connect with like-minded professionals like yourself."
        }
      ];
      
      chrome.storage.sync.set({templates: defaultTemplates}, function() {
        if (isDebugMode) {
          console.log("Default templates saved");
        }
        
        defaultTemplates.forEach(function(template, index) {
          const option = document.createElement('option');
          option.value = index;
          option.textContent = template.name;
          templateSelect.appendChild(option);
        });
      });
    }
  });
}

function displayProfileData(profileData) {
  if (!profileData) return;
  
  const profileDetails = document.getElementById('profile-details');
  
  let html = `<p><strong>Name:</strong> ${profileData.name || 'Not found'}</p>`;
  html += `<p><strong>Title:</strong> ${profileData.title || 'Not found'}</p>`;
  html += `<p><strong>Company:</strong> ${profileData.company || 'Not found'}</p>`;
  
  if (profileData.industry) {
    html += `<p><strong>Industry:</strong> ${profileData.industry}</p>`;
  }
  
  if (profileData.skills && profileData.skills.length > 0) {
    html += `<p><strong>Top Skills:</strong> ${profileData.skills.slice(0, 3).join(', ')}</p>`;
  }
  
  if (profileData.education) {
    html += `<p><strong>Education:</strong> ${profileData.education}</p>`;
  }
  
  if (profileData.mutualConnections && profileData.mutualConnections.length > 0) {
    html += `<p><strong>Mutual Connections:</strong> ${profileData.mutualConnections.slice(0, 2).join(', ')}</p>`;
  }
  
  profileDetails.innerHTML = html;
}

function displayProfileInsights(insights) {
  if (!insights) return;
  
  const suggestionsBox = document.getElementById('ai-suggestions');
  let content = '<div class="insights-header"><strong>🤖 AI Profile Analysis</strong></div>';
  
  // Career level with icon
  if (insights.careerLevel) {
    const levelEmoji = {
      'junior': '🌱',
      'mid-level': '🚀',
      'senior': '⭐',
      'executive': '👑'
    };
    content += `<div class="insight-item"><span class="insight-icon">${levelEmoji[insights.careerLevel] || '💼'}</span>Career Level: ${insights.careerLevel}</div>`;
  }
  
  // Industry focus
  if (insights.industryFocus && insights.industryFocus !== 'general') {
    content += `<div class="insight-item"><span class="insight-icon">🏢</span>Industry: ${insights.industryFocus}</div>`;
  }
  
  // Communication style
  if (insights.communicationStyle) {
    const styleEmoji = {
      'formal': '🎩',
      'casual': '😊',
      'balanced': '⚖️'
    };
    content += `<div class="insight-item"><span class="insight-icon">${styleEmoji[insights.communicationStyle] || '💬'}</span>Communication Style: ${insights.communicationStyle}</div>`;
  }
  
  // Key skills
  if (insights.keySkills && insights.keySkills.length > 0) {
    content += `<div class="insight-item"><span class="insight-icon">🛠️</span>Key Skills: ${insights.keySkills.slice(0, 3).join(', ')}</div>`;
  }
  
  // Connection strategy
  if (insights.connectionStrategy) {
    const strategyNames = {
      'value_proposition': 'Value-focused approach',
      'mutual_interest': 'Shared interests approach',
      'learning_opportunity': 'Learning-focused approach',
      'technical_collaboration': 'Technical collaboration',
      'professional_networking': 'Professional networking'
    };
    
    content += `<div class="insight-item"><span class="insight-icon">🎯</span>Strategy: ${strategyNames[insights.connectionStrategy] || insights.connectionStrategy}</div>`;
  }
  
  // Personality traits
  if (insights.personalityTraits && insights.personalityTraits.length > 0) {
    content += `<div class="insight-item"><span class="insight-icon">✨</span>Traits: ${insights.personalityTraits.join(', ')}</div>`;
  }
  
  suggestionsBox.innerHTML = content;
}

function generatePersonalizedMessage(profileData, profileInsights) {
  const templateSelect = document.getElementById('template-select');
  const messageContent = document.getElementById('message-content');
  
  if (templateSelect.value === '') {
    messageContent.value = 'Please select a template first.';
    messageContent.style.borderColor = '#ff6b6b';
    setTimeout(() => {
      messageContent.style.borderColor = '#ccc';
    }, 2000);
    return;
  }
  
  chrome.storage.sync.get('templates', function(data) {
    if (data.templates && data.templates[templateSelect.value]) {
      const template = data.templates[templateSelect.value];
      
      // Use the AI processor to generate a personalized message
      chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        chrome.tabs.sendMessage(
          tabs[0].id, 
          {
            action: "generatePersonalizedMessage",
            templateData: template,
            profileData: profileData,
            profileInsights: profileInsights
          }, 
          function(response) {
            if (chrome.runtime.lastError) {
              console.log("Error generating message:", chrome.runtime.lastError);
              // Fallback: generate message locally
              generateMessageLocally(template, profileData, profileInsights);
              return;
            }
            
            if (response && response.message) {
              messageContent.value = response.message;
              messageContent.style.borderColor = '#4caf50';
              
              // Update talking points
              if (response.talkingPoints && response.talkingPoints.length > 0) {
                displayTalkingPoints(response.talkingPoints, response.confidence);
              }
              
              // Reset border color after animation
              setTimeout(() => {
                messageContent.style.borderColor = '#ccc';
              }, 2000);
            } else {
              messageContent.value = 'Error: Could not generate personalized message.';
              messageContent.style.borderColor = '#ff6b6b';
            }
          }
        );
      });
    }
  });
}

function generateMessageLocally(template, profileData, profileInsights) {
  // Fallback function to generate message when content script is unavailable
  if (isDebugMode) {
    console.log("Generating message locally");
  }
  
  let message = template.content;
  
  // Basic placeholder replacement
  const firstName = profileData.name ? profileData.name.split(' ')[0] : 'there';
  message = message.replace(/{firstName}/g, firstName);
  message = message.replace(/{name}/g, profileData.name || '[Name]');
  message = message.replace(/{company}/g, profileData.company || '[Company]');
  message = message.replace(/{title}/g, profileData.title || '[Title]');
  
  if (profileInsights) {
    message = message.replace(/{industry}/g, profileInsights.industryFocus || '[Industry]');
    
    if (profileInsights.keySkills && profileInsights.keySkills.length > 0) {
      message = message.replace(/{skill}/g, profileInsights.keySkills[0]);
      message = message.replace(/{skills}/g, profileInsights.keySkills.slice(0, 2).join(' and '));
    }
  }
  
  if (profileData.mutualConnections && profileData.mutualConnections.length > 0) {
    message = message.replace(/{mutualConnection}/g, profileData.mutualConnections[0]);
  }
  
  // Add a simple personalized touch
  if (profileInsights && profileInsights.keySkills && profileInsights.keySkills.length > 0) {
    message += ` Your background in ${profileInsights.keySkills[0]} particularly caught my attention.`;
  }
  
  document.getElementById('message-content').value = message;
  
  // Generate simple talking points
  const talkingPoints = [];
  if (profileInsights && profileInsights.keySkills && profileInsights.keySkills.length > 0) {
    talkingPoints.push(`Discuss their experience with ${profileInsights.keySkills[0]}`);
  }
  if (profileData.company) {
    talkingPoints.push(`Ask about their role at ${profileData.company}`);
  }
  if (profileInsights && profileInsights.industryFocus) {
    talkingPoints.push(`Share insights about ${profileInsights.industryFocus} trends`);
  }
  
  displayTalkingPoints(talkingPoints, 75);
}

function displayTalkingPoints(talkingPoints, confidence) {
  const suggestionsBox = document.getElementById('ai-suggestions');
  let content = `<div class="insights-header"><strong>💡 Conversation Starters</strong>`;
  
  if (confidence) {
    const confidenceColor = confidence >= 80 ? '#4caf50' : confidence >= 60 ? '#ff9800' : '#f44336';
    content += ` <span class="confidence-score" style="color: ${confidenceColor};">(${confidence}% confidence)</span>`;
  }
  
  content += `</div>`;
  
  if (talkingPoints && talkingPoints.length > 0) {
    talkingPoints.forEach(function(point, index) {
      content += `<div class="talking-point"><span class="point-number">${index + 1}.</span> ${point}</div>`;
    });
  } else {
    content += '<div class="talking-point">No specific talking points available.</div>';
  }
  
  suggestionsBox.innerHTML = content;
}

function copyMessageToClipboard() {
  const messageContent = document.getElementById('message-content');
  
  if (!messageContent.value.trim()) {
    messageContent.placeholder = "No message to copy! Generate a message first.";
    setTimeout(() => {
      messageContent.placeholder = "Your personalized message will appear here...";
    }, 3000);
    return;
  }
  
  messageContent.select();
  document.execCommand('copy');
  
  // Show feedback with animation
  const copyButton = document.getElementById('copy-message');
  const originalText = copyButton.textContent;
  copyButton.textContent = '✓ Copied!';
  copyButton.style.backgroundColor = '#4caf50';
  
  setTimeout(function() {
    copyButton.textContent = originalText;
    copyButton.style.backgroundColor = '#0a66c2';
  }, 1500);
  
  // Add a success animation to the textarea
  messageContent.style.borderColor = '#4caf50';
  messageContent.style.boxShadow = '0 0 5px rgba(76, 175, 80, 0.5)';
  
  setTimeout(() => {
    messageContent.style.borderColor = '#ccc';
    messageContent.style.boxShadow = 'none';
  }, 1500);
}

function showTemplateCreator() {
  // Simple template creator using prompts
  // In a real implementation, this would show a modal or dedicated page
  const templateName = prompt('Enter template name:');
  if (!templateName || templateName.trim() === '') return;
  
  const templateInstructions = [
    'Enter template content. You can use these placeholders:',
    '• {firstName} - First name of the person',
    '• {name} - Full name of the person',
    '• {company} - Their company',
    '• {title} - Their job title',
    '• {industry} - Their industry',
    '• {skill} - Their top skill',
    '• {skills} - Multiple skills',
    '• {mutualConnection} - Mutual connection name',
    '',
    'Example: "Hi {firstName}, I noticed your expertise in {skill} at {company}..."'
  ].join('\n');
  
  alert(templateInstructions);
  
  const templateContent = prompt('Enter template content:');
  if (!templateContent || templateContent.trim() === '') return;
  
  chrome.storage.sync.get('templates', function(data) {
    const templates = data.templates || [];
    const newTemplate = {
      name: templateName.trim(),
      content: templateContent.trim(),
      created: new Date().toISOString()
    };
    
    templates.push(newTemplate);
    
    chrome.storage.sync.set({templates: templates}, function() {
      if (isDebugMode) {
        console.log("New template saved:", newTemplate);
      }
      
      // Reload templates in the dropdown
      loadTemplates();
      
      // Auto-select the new template
      setTimeout(() => {
        const templateSelect = document.getElementById('template-select');
        templateSelect.value = templates.length - 1;
        
        // Show success message
        alert(`Template "${templateName}" created successfully!`);
      }, 100);
    });
  });
}

// Helper function to handle errors gracefully
function handleError(error, context) {
  if (isDebugMode) {
    console.error(`Error in ${context}:`, error);
  }
}

// Initialize error handling
window.addEventListener('error', function(event) {
  handleError(event.error, 'Global error handler');
});

// Add some utility functions for enhanced UX
function showLoading(show) {
  const generateButton = document.getElementById('generate-message');
  if (show) {
    generateButton.textContent = 'Generating...';
    generateButton.disabled = true;
    generateButton.style.opacity = '0.7';
  } else {
    generateButton.textContent = 'Generate Message';
    generateButton.disabled = false;
    generateButton.style.opacity = '1';
  }
}