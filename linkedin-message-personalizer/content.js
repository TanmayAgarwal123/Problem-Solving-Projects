// content.js - Enhanced profile extraction with debugging

// Initialize AI processor
let aiProcessor = null;

// Listen for messages from the popup
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  console.log("Content script received message:", request);
  
  if (request.action === "getProfileData") {
    console.log("Extracting profile data...");
    
    // Initialize AI processor if needed
    if (!aiProcessor && window.AIProcessor) {
      aiProcessor = new AIProcessor();
      console.log("AI Processor initialized");
    }
    
    // Extract basic profile data
    const profileData = extractProfileData();
    console.log("Extracted profile data:", profileData);
    
    // Analyze the profile if we have data
    let profileInsights = null;
    if (profileData && aiProcessor) {
      console.log("Analyzing profile with AI...");
      profileInsights = aiProcessor.analyzeProfile(profileData);
      console.log("Profile insights:", profileInsights);
    }
    
    sendResponse({
      profileData: profileData,
      profileInsights: profileInsights
    });
  } else if (request.action === "generatePersonalizedMessage") {
    console.log("Generating personalized message...");
    
    // Initialize AI processor if needed
    if (!aiProcessor && window.AIProcessor) {
      aiProcessor = new AIProcessor();
    }
    
    if (aiProcessor) {
      const result = aiProcessor.generatePersonalizedMessage(
        request.profileInsights,
        request.templateData,
        { profileData: request.profileData }
      );
      
      console.log("Generated message result:", result);
      sendResponse(result);
    } else {
      console.error("AI processor not available");
      sendResponse({
        message: "AI processor not available. Please reload the page.",
        talkingPoints: []
      });
    }
  } else if (request.action === "prepareForExtraction") {
    console.log("Preparing for profile extraction...");
    sendResponse({status: "ready"});
  }
  
  return true;  // Keep the message channel open for async response
});

function extractProfileData() {
  // Check if we're on a profile page
  const currentUrl = window.location.href;
  console.log("Current URL:", currentUrl);
  
  if (!currentUrl.includes('/in/')) {
    console.log("Not on a LinkedIn profile page");
    return null;
  }
  
  console.log("Starting profile data extraction...");
  
  // Wait for page to load completely
  const startTime = Date.now();
  const timeout = 3000; // 3 seconds timeout
  
  // Use multiple selector options for each field to improve reliability
  const profileData = {
    name: extractName(),
    title: extractTitle(),
    company: extractCompany(),
    industry: extractIndustry(),
    education: extractEducation(),
    skills: extractSkills(),
    about: extractAbout(),
    mutualConnections: extractMutualConnections()
  };
  
  console.log("Extraction completed in", Date.now() - startTime, "ms");
  console.log("Final extracted data:", profileData);
  return profileData;
}

function extractName() {
  console.log("Extracting name...");
  
  // Try multiple selectors in order of preference
  const selectors = [
    'h1.text-heading-xlarge',
    '.pv-text-details__left-panel h1',
    '.profile-info .pv-entity__title',
    '.pv-top-card-section__name',
    '.profile-topcard-person-entity__name',
    'h1[data-anonymize="person-name"]',
    '.text-heading-xlarge'
  ];
  
  for (const selector of selectors) {
    try {
      const element = document.querySelector(selector);
      if (element && element.textContent.trim()) {
        const name = element.textContent.trim();
        console.log(`Found name with selector "${selector}":`, name);
        return name;
      }
    } catch (error) {
      console.log(`Error with selector "${selector}":`, error);
    }
  }
  
  // Fallback: Look for any h1 that might contain the name
  console.log("Trying fallback h1 extraction...");
  const h1Elements = document.querySelectorAll('h1');
  for (const h1 of h1Elements) {
    const text = h1.textContent.trim();
    if (text && text.length > 2 && text.length < 50 && !text.includes('LinkedIn')) {
      console.log("Found name in h1 fallback:", text);
      return text;
    }
  }
  
  console.log("Name not found, using default");
  return "LinkedIn User";
}

function extractTitle() {
  console.log("Extracting title...");
  
  const selectors = [
    '.text-body-medium.break-words',
    '.pv-text-details__left-panel .text-body-medium',
    '.pv-top-card-section__headline',
    '.profile-topcard__headline',
    '.pv-entity__summary-title',
    '.pv-top-card--list li:nth-child(2)'
  ];
  
  for (const selector of selectors) {
    try {
      const element = document.querySelector(selector);
      if (element && element.textContent.trim()) {
        const title = element.textContent.trim();
        console.log(`Found title with selector "${selector}":`, title);
        return title;
      }
    } catch (error) {
      console.log(`Error with selector "${selector}":`, error);
    }
  }
  
  console.log("Title not found");
  return null;
}

function extractCompany() {
  console.log("Extracting company...");
  
  const selectors = [
    '.pv-text-details__left-panel .pv-entity__summary-title',
    '.pv-top-card--experience-list-item',
    '.pv-entity__company-details',
    '.pv-entity__secondary-title',
    '.profile-topcard__current-company',
    '[data-field="experience"] .pv-entity__summary-title'
  ];
  
  for (const selector of selectors) {
    try {
      const element = document.querySelector(selector);
      if (element && element.textContent.trim()) {
        const company = element.textContent.trim();
        console.log(`Found company with selector "${selector}":`, company);
        return company;
      }
    } catch (error) {
      console.log(`Error with selector "${selector}":`, error);
    }
  }
  
  // Fallback: Check experience section
  console.log("Trying experience section fallback...");
  try {
    const experienceElements = document.querySelectorAll('[id*="experience"] li, section[data-section="experience"] li');
    if (experienceElements.length > 0) {
      for (const element of experienceElements) {
        const text = element.textContent.trim();
        if (text && text.length > 0) {
          // Try to extract company name from experience text
          const lines = text.split('\n').filter(line => line.trim());
          if (lines.length >= 2) {
            const potentialCompany = lines[1].trim();
            if (potentialCompany && potentialCompany.length < 100) {
              console.log("Found company in experience fallback:", potentialCompany);
              return potentialCompany;
            }
          }
        }
      }
    }
  } catch (error) {
    console.log("Error in experience fallback:", error);
  }
  
  console.log("Company not found");
  return null;
}

function extractIndustry() {
  console.log("Extracting industry...");
  
  // Industry isn't always directly available, try to infer it
  const aboutText = extractAbout();
  if (aboutText) {
    const industryKeywords = [
      'industry', 'sector', 'field', 'domain', 'specializing in', 'working in'
    ];
    
    const text = aboutText.toLowerCase();
    for (const keyword of industryKeywords) {
      const index = text.indexOf(keyword);
      if (index !== -1) {
        // Extract text around the keyword
        const start = Math.max(0, index - 10);
        const end = Math.min(text.length, index + 60);
        const context = text.substring(start, end);
        
        // Try to extract the industry name
        const patterns = [
          new RegExp(`${keyword}[:\\s]+([\w\\s]+)`, 'i'),
          new RegExp(`([\w\\s]+)\\s+${keyword}`, 'i')
        ];
        
        for (const pattern of patterns) {
          const matches = context.match(pattern);
          if (matches && matches[1]) {
            const industry = matches[1].trim();
            if (industry.length > 2 && industry.length < 50) {
              console.log("Found industry:", industry);
              return industry;
            }
          }
        }
      }
    }
  }
  
  console.log("Industry not found");
  return null;
}

function extractEducation() {
  console.log("Extracting education...");
  
  const selectors = [
    '[id*="education"] .pv-entity__degree-name',
    '[id*="education"] .pv-entity__school-name',
    '[data-section="education"] .pv-entity__degree-name',
    '[data-section="education"] .pv-entity__school-name',
    '.education__item .education__school',
    '.education__item .education__degree'
  ];
  
  for (const selector of selectors) {
    try {
      const element = document.querySelector(selector);
      if (element && element.textContent.trim()) {
        const education = element.textContent.trim();
        console.log(`Found education with selector "${selector}":`, education);
        return education;
      }
    } catch (error) {
      console.log(`Error with selector "${selector}":`, error);
    }
  }
  
  // Fallback: Look for education section
  console.log("Trying education section fallback...");
  try {
    const educationSections = document.querySelectorAll('section[id*="education"], section[data-section="education"]');
    if (educationSections.length > 0) {
      const text = educationSections[0].textContent.trim();
      const lines = text.split('\n').filter(line => line.trim());
      if (lines.length > 0) {
        const education = lines[0].trim();
        if (education && education.length < 100) {
          console.log("Found education in fallback:", education);
          return education;
        }
      }
    }
  } catch (error) {
    console.log("Error in education fallback:", error);
  }
  
  console.log("Education not found");
  return null;
}

function extractSkills() {
  console.log("Extracting skills...");
  
  const skills = [];
  
  // Try multiple skill selectors
  const skillSelectors = [
    '[id*="skills"] .pv-skill-category-entity__name-text',
    '[data-section="skills"] .pv-skill-entity__skill-name',
    '.skills-section .pv-skill-item__skill-name-text',
    '[id*="skills"] span[aria-hidden="true"]',
    '.skill-category-card .pv-skill-category-entity__name-text'
  ];
  
  for (const selector of skillSelectors) {
    try {
      const elements = document.querySelectorAll(selector);
      console.log(`Found ${elements.length} elements with selector "${selector}"`);
      
      if (elements.length > 0) {
        elements.forEach(element => {
          const skill = element.textContent.trim();
          if (skill && skill.length > 1 && skill.length < 50 && !skills.includes(skill)) {
            skills.push(skill);
          }
        });
        
        if (skills.length > 0) {
          console.log(`Found skills with selector "${selector}":`, skills);
          break;
        }
      }
    } catch (error) {
      console.log(`Error with selector "${selector}":`, error);
    }
  }
  
  // Fallback: Extract skills from any section mentioning "skills"
  if (skills.length === 0) {
    console.log("Trying skills section fallback...");
    try {
      const skillSections = document.querySelectorAll('section[id*="skill"], section[class*="skill"]');
      skillSections.forEach(section => {
        const spans = section.querySelectorAll('span');
        spans.forEach(span => {
          const text = span.textContent.trim();
          if (text && text.length > 1 && text.length < 30 && !skills.includes(text) &&
              !text.includes('skills') && !text.includes('Show') && !text.includes('See')) {
            skills.push(text);
          }
        });
      });
      
      if (skills.length > 0) {
        console.log("Found skills in fallback:", skills);
      }
    } catch (error) {
      console.log("Error in skills fallback:", error);
    }
  }
  
  const finalSkills = skills.slice(0, 10); // Limit to 10 skills
  console.log("Final skills array:", finalSkills);
  return finalSkills.length > 0 ? finalSkills : null;
}

function extractAbout() {
  console.log("Extracting about section...");
  
  const selectors = [
    '[id*="about"] .pv-about__summary-text',
    '[data-section="summary"] .pv-about__summary-text',
    '.pv-about-section .pv-about__summary-text',
    '.profile-section-card__contents p',
    '.about-section p',
    '[id*="about"] .inline-show-more-text',
    '.pv-about__summary-text .visually-hidden'
  ];
  
  for (const selector of selectors) {
    try {
      const element = document.querySelector(selector);
      if (element && element.textContent.trim()) {
        const about = element.textContent.trim();
        console.log(`Found about with selector "${selector}" (${about.length} chars)`);
        return about;
      }
    } catch (error) {
      console.log(`Error with selector "${selector}":`, error);
    }
  }
  
  // Fallback: Look for any section that might contain the about text
  console.log("Trying about section fallback...");
  try {
    const aboutSections = document.querySelectorAll('section[id*="about"], section[class*="about"]');
    if (aboutSections.length > 0) {
      const text = aboutSections[0].textContent.trim();
      if (text && text.length > 50) {
        console.log("Found about in fallback:", text.substring(0, 100) + "...");
        return text;
      }
    }
  } catch (error) {
    console.log("Error in about fallback:", error);
  }
  
  console.log("About section not found");
  return null;
}

function extractMutualConnections() {
  console.log("Extracting mutual connections...");
  
  const mutualConnections = [];
  
  const selectors = [
    '.pv-shared-connections-section',
    '.shared-connections',
    '[data-section="sharedConnections"]',
    '.pv-top-card-v2-ctas .pv-shared-connections'
  ];
  
  for (const selector of selectors) {
    try {
      const element = document.querySelector(selector);
      if (element) {
        console.log(`Found mutual connections section with selector "${selector}"`);
        
        const connectionElements = element.querySelectorAll('li, a, span');
        connectionElements.forEach(el => {
          const name = el.textContent.trim();
          if (name && name.length > 2 && name.length < 50 && 
              !name.includes('mutual') && !name.includes('connection') &&
              !mutualConnections.includes(name)) {
            mutualConnections.push(name);
          }
        });
        
        if (mutualConnections.length > 0) {
          console.log("Found mutual connections:", mutualConnections);
          break;
        }
      }
    } catch (error) {
      console.log(`Error with selector "${selector}":`, error);
    }
  }
  
  const finalConnections = mutualConnections.slice(0, 5); // Limit to 5 connections
  console.log("Final mutual connections:", finalConnections);
  return finalConnections.length > 0 ? finalConnections : null;
}

// Helper function to wait for elements to load
function waitForElement(selector, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const element = document.querySelector(selector);
    if (element) {
      resolve(element);
      return;
    }
    
    const observer = new MutationObserver(() => {
      const element = document.querySelector(selector);
      if (element) {
        observer.disconnect();
        resolve(element);
      }
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
    
    setTimeout(() => {
      observer.disconnect();
      reject(new Error(`Element ${selector} not found within ${timeout}ms`));
    }, timeout);
  });
}

// Initialize when the page loads
console.log("LinkedIn Message Personalizer content script loaded");