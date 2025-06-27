/**
 * AI Processor Module for LinkedIn Message Personalizer
 * Handles profile analysis and message personalization
 */

class AIProcessor {
  constructor() {
    this.debug = true; // Enable debugging
    
    if (this.debug) {
      console.log("AI Processor initialized");
    }
    
    // Initialize any required resources
    this.keyPhrases = new Map([
      ['software engineer', ['programming', 'development', 'coding', 'software architecture']],
      ['data scientist', ['machine learning', 'data analysis', 'algorithms', 'statistics']],
      ['product manager', ['product strategy', 'user experience', 'roadmap', 'agile']],
      ['marketing', ['campaigns', 'branding', 'content strategy', 'growth']],
      ['sales', ['business development', 'client relationships', 'negotiations', 'revenue']],
      ['designer', ['user interface', 'user experience', 'creative design', 'visual design']],
      ['consultant', ['strategy', 'advisory', 'business consulting', 'problem solving']],
      ['analyst', ['data analysis', 'research', 'insights', 'reporting']],
      ['manager', ['team leadership', 'project management', 'strategic planning', 'operations']]
    ]);
    
    // Industry-specific talking points
    this.industryTopics = {
      'technology': [
        'digital transformation', 
        'emerging tech trends',
        'innovation culture',
        'software development',
        'AI and machine learning'
      ],
      'finance': [
        'fintech disruption',
        'market analysis',
        'investment strategies',
        'financial technology',
        'regulatory compliance'
      ],
      'healthcare': [
        'health tech innovations',
        'patient care improvements',
        'medical research',
        'digital health',
        'healthcare analytics'
      ],
      'education': [
        'e-learning platforms',
        'educational technology',
        'skill development',
        'online learning',
        'curriculum innovation'
      ],
      'consulting': [
        'business strategy',
        'digital consulting',
        'process optimization',
        'change management',
        'business transformation'
      ],
      'media': [
        'content strategy',
        'digital media',
        'brand storytelling',
        'social media',
        'audience engagement'
      ]
    };
  }
  
  // Debugging helper
  logDebug(message, data) {
    if (this.debug) {
      console.log(`[AIProcessor] ${message}`, data);
    }
  }
  
  /**
   * Analyze a LinkedIn profile and extract key insights
   * @param {Object} profileData - Raw profile data
   * @return {Object} Profile insights
   */
  analyzeProfile(profileData) {
    this.logDebug("Analyzing profile", profileData);
    
    if (!profileData) return null;
    
    // Extract insights from various profile sections
    const insights = {
      keySkills: this.extractKeySkills(profileData),
      topicInterests: this.identifyTopicInterests(profileData),
      careerLevel: this.determineCareerLevel(profileData),
      industryFocus: this.detectIndustryFocus(profileData),
      recentActivities: this.analyzeRecentActivity(profileData),
      connectionStrategy: this.suggestConnectionStrategy(profileData),
      communicationStyle: this.determineCommunicationStyle(profileData),
      personalityTraits: this.extractPersonalityTraits(profileData)
    };
    
    this.logDebug("Profile insights generated", insights);
    return insights;
  }
  
  /**
   * Generate personalized message suggestions based on profile insights
   * @param {Object} profileInsights - Processed profile insights
   * @param {Object} templateData - Selected message template
   * @param {Object} userContext - Additional context
   * @return {Object} Personalized message data
   */
  generatePersonalizedMessage(profileInsights, templateData, userContext = {}) {
    this.logDebug("Generating personalized message", { profileInsights, templateData, userContext });
    
    if (!profileInsights || !templateData) {
      return {
        message: "Couldn't generate a personalized message. Please check the profile data.",
        talkingPoints: [],
        confidence: 0
      };
    }
    
    // Generate talking points
    const talkingPoints = this.generateTalkingPoints(profileInsights);
    
    // Personalize the message template
    let personalizedMessage = this.customizeMessageTemplate(
      templateData.content,
      profileInsights,
      userContext
    );
    
    // Add a personalized element based on insights
    personalizedMessage = this.enhanceWithInsights(personalizedMessage, profileInsights);
    
    // Calculate confidence score
    const confidence = this.calculateConfidenceScore(profileInsights, userContext);
    
    const result = {
      message: personalizedMessage,
      talkingPoints: talkingPoints,
      confidence: confidence
    };
    
    this.logDebug("Generated personalized message", result);
    return result;
  }
  
  /**
   * Extract key skills from profile data
   */
  extractKeySkills(profileData) {
    const skills = [];
    
    // Extract from explicit skills section
    if (profileData.skills && profileData.skills.length > 0) {
      skills.push(...profileData.skills.slice(0, 5));
    }
    
    // Extract from title and about section using keyword matching
    if (profileData.title) {
      const title = profileData.title.toLowerCase();
      
      // Check for key roles and add related skills
      for (const [role, relatedSkills] of this.keyPhrases.entries()) {
        if (title.includes(role)) {
          // Only add 1-2 inferred skills to avoid overwhelming
          skills.push(...relatedSkills.slice(0, 2));
          break;
        }
      }
    }
    
    // Extract from about section
    if (profileData.about) {
      const about = profileData.about.toLowerCase();
      const skillKeywords = ['experienced in', 'skilled in', 'expertise in', 'proficient in'];
      
      for (const keyword of skillKeywords) {
        const index = about.indexOf(keyword);
        if (index !== -1) {
          // Extract skills mentioned after these keywords
          const skillText = about.substring(index + keyword.length, index + keyword.length + 100);
          const extractedSkills = skillText.match(/\b[A-Za-z\s]+\b/g);
          if (extractedSkills) {
            skills.push(...extractedSkills.slice(0, 2));
            break;
          }
        }
      }
    }
    
    // Remove duplicates and clean up
    const uniqueSkills = [...new Set(skills)].filter(skill => 
      skill && skill.trim().length > 2 && skill.trim().length < 30
    );
    
    return uniqueSkills.slice(0, 5); // Return top 5 skills
  }
  
  /**
   * Identify topics the person might be interested in
   */
  identifyTopicInterests(profileData) {
    const interests = [];
    
    // Infer from industry
    const industry = this.detectIndustryFocus(profileData);
    if (industry && this.industryTopics[industry]) {
      interests.push(...this.industryTopics[industry].slice(0, 2));
    }
    
    // Infer from about section
    if (profileData.about) {
      const aboutText = profileData.about.toLowerCase();
      
      // Check for passion indicators
      const passionPhrases = [
        'passionate about', 'interested in', 'focus on', 'specializing in',
        'enthusiastic about', 'dedicated to', 'committed to', 'working on'
      ];
      
      for (const phrase of passionPhrases) {
        const index = aboutText.indexOf(phrase);
        if (index !== -1) {
          // Extract text after the phrase until the next period or comma
          const endIndex = Math.min(
            aboutText.indexOf('.', index) !== -1 ? aboutText.indexOf('.', index) : aboutText.length,
            aboutText.indexOf(',', index) !== -1 ? aboutText.indexOf(',', index) : aboutText.length,
            index + 100
          );
          
          const relevantText = aboutText.substring(index + phrase.length, endIndex);
          
          // Add as an interest if it's substantial
          if (relevantText.length > 5) {
            interests.push(relevantText.trim());
          }
          
          break;
        }
      }
    }
    
    // Extract from title
    if (profileData.title) {
      const title = profileData.title.toLowerCase();
      const titleTopics = ['innovation', 'strategy', 'growth', 'development', 'technology', 'data', 'design'];
      
      for (const topic of titleTopics) {
        if (title.includes(topic)) {
          interests.push(topic);
        }
      }
    }
    
    return [...new Set(interests)].slice(0, 3);
  }
  
  /**
   * Determine approximate career level
   */
  determineCareerLevel(profileData) {
    if (!profileData.title) return 'mid-level'; // Default assumption
    
    const title = profileData.title.toLowerCase();
    
    // Executive level indicators
    const executiveKeywords = [
      'ceo', 'cto', 'cfo', 'chief', 'president', 'vice president', 'vp',
      'director', 'head of', 'founder', 'co-founder'
    ];
    
    // Senior level indicators
    const seniorKeywords = [
      'senior', 'lead', 'principal', 'architect', 'staff', 'expert',
      'specialist', 'manager', 'team lead'
    ];
    
    // Junior level indicators
    const juniorKeywords = [
      'junior', 'associate', 'assistant', 'intern', 'trainee',
      'entry', 'graduate', 'analyst'
    ];
    
    if (executiveKeywords.some(keyword => title.includes(keyword))) {
      return 'executive';
    } else if (seniorKeywords.some(keyword => title.includes(keyword))) {
      return 'senior';
    } else if (juniorKeywords.some(keyword => title.includes(keyword))) {
      return 'junior';
    } else {
      return 'mid-level';
    }
  }
  
  /**
   * Detect industry focus
   */
  detectIndustryFocus(profileData) {
    if (profileData.industry) return profileData.industry.toLowerCase();
    
    // If no explicit industry, infer from company and title
    const industryKeywords = {
      'technology': [
        'tech', 'software', 'digital', 'it ', 'computing', 'cyber', 'cloud',
        'saas', 'AI', 'machine learning', 'data science', 'engineering'
      ],
      'finance': [
        'bank', 'financ', 'invest', 'trading', 'capital', 'wealth', 'asset',
        'insurance', 'fintech', 'payment', 'credit'
      ],
      'healthcare': [
        'health', 'medical', 'pharma', 'biotech', 'life sciences', 'care',
        'hospital', 'clinic', 'therapeutic', 'medicine'
      ],
      'education': [
        'edu', 'teach', 'school', 'university', 'college', 'learning',
        'training', 'academic', 'research'
      ],
      'consulting': [
        'consult', 'advisory', 'strategy', 'management consulting',
        'professional services', 'business consulting'
      ],
      'media': [
        'media', 'marketing', 'advertising', 'communications', 'public relations',
        'content', 'digital marketing', 'social media'
      ]
    };
    
    const textToAnalyze = `${profileData.title || ''} ${profileData.company || ''} ${profileData.about || ''}`.toLowerCase();
    
    for (const [industry, keywords] of Object.entries(industryKeywords)) {
      const matchCount = keywords.filter(keyword => textToAnalyze.includes(keyword)).length;
      if (matchCount >= 2) {
        return industry;
      }
    }
    
    // Single keyword match as fallback
    for (const [industry, keywords] of Object.entries(industryKeywords)) {
      if (keywords.some(keyword => textToAnalyze.includes(keyword))) {
        return industry;
      }
    }
    
    return 'general';
  }
  
  /**
   * Analyze recent activity (placeholder)
   */
  analyzeRecentActivity(profileData) {
    // In a real implementation, this would analyze posts and activity
    // For now, return a placeholder
    return [];
  }
  
  /**
   * Suggest connection strategy based on profile
   */
  suggestConnectionStrategy(profileData) {
    const careerLevel = this.determineCareerLevel(profileData);
    const industryFocus = this.detectIndustryFocus(profileData);
    
    // Different strategies based on seniority and context
    if (careerLevel === 'executive') {
      return 'value_proposition';
    } else if (careerLevel === 'senior') {
      return 'mutual_interest';
    } else if (careerLevel === 'junior') {
      return 'learning_opportunity';
    } else {
      // Mid-level - choose based on industry
      if (industryFocus === 'technology') {
        return 'technical_collaboration';
      } else {
        return 'professional_networking';
      }
    }
  }
  
  /**
   * Determine communication style
   */
  determineCommunicationStyle(profileData) {
    if (!profileData.about) return 'balanced';
    
    const about = profileData.about.toLowerCase();
    
    // Formal indicators
    const formalIndicators = [
      'extensive experience', 'proven track record', 'demonstrated',
      'accomplished', 'expertise', 'professional', 'strategic'
    ];
    
    // Casual indicators
    const casualIndicators = [
      'passionate', 'love', 'excited', 'fun', 'enjoy', 'creative',
      'innovative', 'dynamic'
    ];
    
    const formalCount = formalIndicators.filter(indicator => about.includes(indicator)).length;
    const casualCount = casualIndicators.filter(indicator => about.includes(indicator)).length;
    
    if (formalCount > casualCount + 1) {
      return 'formal';
    } else if (casualCount > formalCount + 1) {
      return 'casual';
    } else {
      return 'balanced';
    }
  }
  
  /**
   * Extract personality traits from profile
   */
  extractPersonalityTraits(profileData) {
    const traits = [];
    
    if (!profileData.about) return traits;
    
    const about = profileData.about.toLowerCase();
    
    const traitKeywords = {
      'analytical': ['analysis', 'data-driven', 'research', 'analytical'],
      'creative': ['creative', 'innovative', 'design', 'artistic'],
      'leadership': ['lead', 'manage', 'team', 'leadership'],
      'collaborative': ['collaborate', 'team player', 'partnership', 'cooperation'],
      'ambitious': ['achieve', 'goal', 'drive', 'ambitious'],
      'detail-oriented': ['detail', 'precision', 'accuracy', 'meticulous']
    };
    
    for (const [trait, keywords] of Object.entries(traitKeywords)) {
      if (keywords.some(keyword => about.includes(keyword))) {
        traits.push(trait);
      }
    }
    
    return traits.slice(0, 3);
  }
  
  /**
   * Generate relevant talking points
   */
  generateTalkingPoints(profileInsights) {
    const talkingPoints = [];
    
    // Add skill-based talking points
    if (profileInsights.keySkills && profileInsights.keySkills.length > 0) {
      talkingPoints.push(`Ask about their experience with ${profileInsights.keySkills[0]}`);
      
      if (profileInsights.keySkills.length > 1) {
        talkingPoints.push(`Mention your interest in ${profileInsights.keySkills[1]}`);
      }
    }
    
    // Add industry-based talking points
    if (profileInsights.industryFocus && profileInsights.industryFocus !== 'general') {
      talkingPoints.push(`Discuss recent trends in ${profileInsights.industryFocus}`);
    }
    
    // Add career-level appropriate talking points
    switch (profileInsights.connectionStrategy) {
      case 'value_proposition':
        talkingPoints.push('Briefly mention how you might add value to their network');
        break;
      case 'mutual_interest':
        talkingPoints.push('Highlight a shared professional interest or experience');
        break;
      case 'learning_opportunity':
        talkingPoints.push('Express interest in learning from their experience');
        break;
      case 'technical_collaboration':
        talkingPoints.push('Suggest potential for technical collaboration or knowledge sharing');
        break;
      case 'professional_networking':
        talkingPoints.push('Focus on mutual professional growth and networking');
        break;
    }
    
    // Add personality-based talking points
    if (profileInsights.personalityTraits && profileInsights.personalityTraits.length > 0) {
      const trait = profileInsights.personalityTraits[0];
      talkingPoints.push(`Appreciate their ${trait} approach to work`);
    }
    
    // Add interest-based talking points
    if (profileInsights.topicInterests && profileInsights.topicInterests.length > 0) {
      talkingPoints.push(`Reference their interest in ${profileInsights.topicInterests[0]}`);
    }
    
    return talkingPoints.slice(0, 5); // Return top 5 talking points
  }
  
  /**
   * Customize message template with profile data
   */
  customizeMessageTemplate(templateContent, profileInsights, userContext) {
    let message = templateContent;
    
    // Replace basic placeholders
    if (userContext.profileData) {
      const firstName = userContext.profileData.name ? 
        userContext.profileData.name.split(' ')[0] : 'there';
      
      message = message.replace(/{firstName}/g, firstName);
      message = message.replace(/{name}/g, userContext.profileData.name || '[Name]');
      message = message.replace(/{company}/g, userContext.profileData.company || '[Company]');
      message = message.replace(/{title}/g, userContext.profileData.title || '[Title]');
      message = message.replace(/{industry}/g, profileInsights.industryFocus || '[Industry]');
      
      // Replace skill placeholders
      if (profileInsights.keySkills && profileInsights.keySkills.length > 0) {
        message = message.replace(/{skill}/g, profileInsights.keySkills[0]);
        message = message.replace(/{skills}/g, profileInsights.keySkills.slice(0, 2).join(' and '));
      }
      
      // Replace mutual connections if template includes them
      if (userContext.profileData.mutualConnections && userContext.profileData.mutualConnections.length > 0) {
        message = message.replace(/{mutualConnection}/g, userContext.profileData.mutualConnections[0]);
      }
    }
    
    return message;
  }
  
  /**
   * Enhance message with profile insights
   */
  enhanceWithInsights(message, profileInsights) {
    let enhancedMessage = message;
    
    // Add a personalized element based on career level and connection strategy
    switch (profileInsights.connectionStrategy) {
      case 'value_proposition':
        if (profileInsights.keySkills && profileInsights.keySkills.length > 0) {
          enhancedMessage += ` I've been working on projects related to ${profileInsights.keySkills[0]} and would love to share insights that might be valuable to your work.`;
        } else {
          enhancedMessage += ` I believe we could create mutual value by connecting and sharing our professional experiences.`;
        }
        break;
        
      case 'mutual_interest':
        if (profileInsights.topicInterests && profileInsights.topicInterests.length > 0) {
          enhancedMessage += ` I noticed your work in ${profileInsights.topicInterests[0]}, which aligns perfectly with my current projects.`;
        } else if (profileInsights.industryFocus) {
          enhancedMessage += ` I see we both work in ${profileInsights.industryFocus}, and I'd love to exchange insights about industry trends.`;
        }
        break;
        
      case 'learning_opportunity':
        if (profileInsights.keySkills && profileInsights.keySkills.length > 0) {
          enhancedMessage += ` I'm particularly interested in learning more about your experience with ${profileInsights.keySkills[0]}.`;
        } else {
          enhancedMessage += ` I'd love to learn from your experience and perspective in the field.`;
        }
        break;
        
      case 'technical_collaboration':
        if (profileInsights.keySkills && profileInsights.keySkills.length > 0) {
          enhancedMessage += ` I've been working with ${profileInsights.keySkills[0]} as well, and I think we could have some interesting technical discussions.`;
        } else {
          enhancedMessage += ` I believe there could be great opportunities for technical collaboration between us.`;
        }
        break;
        
      case 'professional_networking':
        enhancedMessage += ` I'm always looking to connect with like-minded professionals, and I believe we could support each other's career growth.`;
        break;
    }
    
    return enhancedMessage;
  }
  
  /**
   * Calculate confidence score for the personalization
   */
  calculateConfidenceScore(profileInsights, userContext) {
    let score = 0;
    let maxScore = 0;
    
    // Check if we have profile data
    if (userContext.profileData) {
      if (userContext.profileData.name) { score += 10; }
      if (userContext.profileData.title) { score += 15; }
      if (userContext.profileData.company) { score += 10; }
      if (userContext.profileData.about) { score += 20; }
      maxScore += 55;
    }
    
    // Check insights quality
    if (profileInsights.keySkills && profileInsights.keySkills.length > 0) { score += 15; }
    if (profileInsights.industryFocus && profileInsights.industryFocus !== 'general') { score += 10; }
    if (profileInsights.topicInterests && profileInsights.topicInterests.length > 0) { score += 10; }
    if (profileInsights.personalityTraits && profileInsights.personalityTraits.length > 0) { score += 10; }
    maxScore += 45;
    
    // Return percentage
    return Math.round((score / maxScore) * 100);
  }
}

// Make the class available to other files
window.AIProcessor = AIProcessor;