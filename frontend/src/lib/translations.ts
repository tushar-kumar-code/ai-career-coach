export type Language = 'en' | 'hi';

export interface Translations {
  [key: string]: string;
}

export const translations: Record<Language, Translations> = {
  en: {
    // Brand & App
    'app.title': 'AI Career Coach',
    'app.subtitle': 'Personal Twin Platform',
    'app.cockpit': 'AI Career Coach Cockpit',

    // Navigation / Sidebar
    'nav.dashboard': 'Dashboard',
    'nav.assessment': 'Discovery Assessment',
    'nav.profile': 'Digital Twin Profile',
    'nav.resume': 'Resume & ATS',
    'nav.skills': 'Skill Matrix',
    'nav.jobs': 'Job Engine',
    'nav.roadmap': 'Roadmap & Tasks',
    'nav.practice': 'Micro Practice',
    'nav.interview': 'Mock Interview',
    'nav.placement': 'Placement Readiness',
    'nav.progress': 'Progress & Readiness',
    'nav.chat': 'AI Career Coach',
    'nav.guide': 'How to Use / Guide',
    'nav.settings': 'Settings',
    'nav.signOut': 'Sign Out',
    'nav.authenticatedAs': 'Candidate Account',

    // Header
    'header.cockpit': 'AI Career Coach Cockpit',
    'header.online': 'Online',
    'header.connected': 'Connected',
    'header.setAiKey': 'Set AI Key',
    'header.activeKey': 'Active',
    'header.theme': 'Theme',
    'header.language': 'Language',

    // Settings General
    'settings.title': 'Settings',
    'settings.subtitle': 'Manage your AI configuration, language, account, and preferences',
    'settings.tabAi': 'AI & API Key',
    'settings.tabLanguage': 'Language / भाषा',
    'settings.tabAccount': 'Account',
    'settings.tabNotifications': 'Notifications',
    'settings.tabAppearance': 'Appearance',
    'settings.tabAbout': 'About',

    // Settings - Language Tab
    'settings.langTitle': 'Language Choice / भाषा चयन',
    'settings.langDesc': 'Select your preferred language. The chosen language will be applied across the entire web application.',
    'settings.langSelectEn': 'English (अंग्रेज़ी)',
    'settings.langSelectEnSub': 'Default language for all interfaces, navigation, and tools.',
    'settings.langSelectHi': 'Hindi (हिंदी)',
    'settings.langSelectHiSub': 'संपूर्ण वेब ऐप में हिंदी भाषा का उपयोग करें।',
    'settings.langCurrentActive': 'Currently Active Language',
    'settings.langSuccessMsg': 'Language updated successfully! The entire web app will now display in',
    'settings.langPreviewTitle': 'Live Interface Preview / पूर्वावलोकन',
    'settings.langPreviewText': 'Welcome to AI Career Coach! Your personal career guidance platform.',

    // Settings - AI Tab
    'settings.aiTitle': 'AI Engine Configuration',
    'settings.aiDesc': 'Select your AI provider and manage your API key. Used for Career Coach Chat, Mock Interviews, Resume Analysis, and Roadmap Generation.',
    'settings.aiStatusActive': 'AI Active',
    'settings.aiStatusNoKey': 'No API Key configured',
    'settings.aiProviderLabel': 'AI Provider',
    'settings.apiKeyLabel': 'API Key',
    'settings.apiKeyPlaceholder': 'Enter your API key',
    'settings.testKey': 'Test Key',
    'settings.saveKey': 'Save Key',
    'settings.clearKey': 'Clear Key',
    'settings.keySavedSuccess': 'API Key saved and activated for all AI features!',

    // Settings - Account Tab
    'settings.accountTitle': 'Account Details',
    'settings.accountDesc': 'View your account credentials and personal profile details.',
    'settings.fullName': 'Full Name',
    'settings.emailAddress': 'Email Address',
    'settings.accountStatus': 'Account Status',
    'settings.authentication': 'Authentication',
    'settings.statusActive': 'Active',
    'settings.signOutAccount': 'Sign Out of Account',

    // Settings - Notifications Tab
    'settings.notifTitle': 'Notification Preferences',
    'settings.notifDesc': 'Control which activity notifications and reminders you receive.',
    'settings.weeklyReport': 'Weekly Progress Report',
    'settings.weeklyReportSub': 'Receive a summary of your career progress every week',
    'settings.interviewReminder': 'Interview Practice Reminders',
    'settings.interviewReminderSub': 'Get reminded to practice mock interviews regularly',
    'settings.roadmapProgress': 'Roadmap Milestone Alerts',
    'settings.roadmapProgressSub': 'Notify me when I reach a roadmap milestone',
    'settings.savePreferences': 'Save Preferences',
    'settings.preferencesSaved': 'Saved!',

    // Settings - Appearance Tab
    'settings.appearanceTitle': 'Appearance & Theme Studio',
    'settings.appearanceDesc': 'Customize the platform theme, ambient glow, and color palette in real-time.',
    'settings.resetDefaults': 'Reset Defaults',
    'settings.themePresets': 'Theme Presets (Instant Live Switch)',
    'settings.accentColor': 'Accent Color Highlight',
    'settings.visualEffects': 'Layout & Visual Effects',

    // Settings - About Tab
    'settings.aboutTitle': 'About AI Career Coach',
    'settings.aboutDesc': 'An AI-powered personal career coach and digital twin tracking system built to accelerate career growth.',
    'settings.version': 'Version',
    'settings.techStack': 'Technology Stack',
    'settings.builtWith': 'Built with Next.js, TypeScript, FastAPI & AI APIs.',

    // Common Buttons & Labels
    'common.save': 'Save',
    'common.saved': 'Saved!',
    'common.cancel': 'Cancel',
    'common.close': 'Close',
    'common.loading': 'Loading...',
    'common.active': 'Active',
    'common.recommended': 'Recommended',
    'common.view': 'View',
    'common.edit': 'Edit',
    'common.delete': 'Delete',
    'common.back': 'Back',
    'common.continue': 'Continue',
    'common.start': 'Start',
    'common.status': 'Status',
    'common.action': 'Action',

    // Dashboard
    'dashboard.welcome': 'Welcome back',
    'dashboard.subtitle': 'Your AI-powered career growth cockpit & digital twin tracking',
    'dashboard.readinessScore': 'Career Readiness Score',
    'dashboard.targetRole': 'Target Role',
    'dashboard.skillsMastered': 'Skills Mastered',
    'dashboard.activeRoadmap': 'Active Roadmap',
    'dashboard.quickActions': 'Quick Actions',
    'dashboard.startAssessment': 'Start Assessment',
    'dashboard.practiceInterview': 'Practice Mock Interview',
    'dashboard.analyzeResume': 'Tailor Resume',
    'dashboard.chatCoach': 'Talk to Career Coach',
    'dashboard.onboardingChecklist': 'Onboarding Checklist',

    // Assessment Page
    'assessment.title': 'Interactive Career Discovery Assessment',
    'assessment.questionStep': 'Question',
    'assessment.of': 'of',
    'assessment.instruction': 'Please select the option that best describes your instinctual approach:',
    'assessment.nextBtn': 'Next Question →',
    'assessment.submitBtn': 'Complete Assessment & Generate AI Analysis ✨',
    'assessment.submitting': 'Recording Answer...',
    'assessment.loadingSession': 'Loading Career Discovery Session...',
    'assessment.analyzingTitle': 'Analyzing Your Career Discovery Profile',
    'assessment.analyzingDesc': 'Gemini AI is evaluating your problem solving, logical reasoning, and work style preferences against our 12 structured career role frameworks...',
    'assessment.resultsTitle': 'Your AI Career Discovery Profile',
    'assessment.resultsSubtitle': 'Evidence-backed career evaluation powered by Gemini AI. You remain in complete control of your target career selection.',
    'assessment.retake': 'Retake Assessment',
    'assessment.archetypeLabel': 'Career Archetype',
    'assessment.motivationLabel': 'Motivation & Driver',
    'assessment.currentTarget': 'Current Selected Target',
    'assessment.noneSelected': 'None Selected',
    'assessment.recommendedTitle': 'AI Recommended Career Matches',
    'assessment.setTarget': 'Set Target Role',
    'assessment.activeTarget': 'Active Target',
    'assessment.exploreCompare': 'Explore & Compare',
    'assessment.nextStepResume': 'Next Step: Upload & Scan Your Resume',
    'assessment.uploadResumeBtn': 'Upload Resume →',

    // Modals
    'modal.apiKeyTitle': 'Configure AI API Key',
    'modal.apiKeyDesc': 'Add your Groq or Google Gemini API key to enable AI coaching features.',
    'modal.themeTitle': 'Customize Theme & Appearance',
    'modal.themeDesc': 'Tailor the interface visual theme and accent colors.',
  },
  hi: {
    // Brand & App
    'app.title': 'एआई करियर कोच',
    'app.subtitle': 'व्यक्तिगत डिजिटल ट्विन प्लेटफॉर्म',
    'app.cockpit': 'एआई करियर कोच कॉकपिट',

    // Navigation / Sidebar
    'nav.dashboard': 'डैशबोर्ड',
    'nav.assessment': 'डिस्कवरी असेसमेंट',
    'nav.profile': 'डिजिटल ट्विन प्रोफाइल',
    'nav.resume': 'रेज़्यूमे और एटीएस',
    'nav.skills': 'स्किल मैट्रिक्स',
    'nav.jobs': 'जॉब इंजन',
    'nav.roadmap': 'रोडमैप और टास्क',
    'nav.practice': 'माइक्रो प्रैक्टिस',
    'nav.interview': 'मॉक इंटरव्यू',
    'nav.placement': 'प्लेसमेंट तैयारी',
    'nav.progress': 'प्रगति और तैयारी',
    'nav.chat': 'एआई करियर कोच',
    'nav.guide': 'उपयोग कैसे करें / गाइड',
    'nav.settings': 'सेटिंग्स',
    'nav.signOut': 'साइन आउट',
    'nav.authenticatedAs': 'उम्मीदवार खाता',

    // Header
    'header.cockpit': 'एआई करियर कोच कॉकपिट',
    'header.online': 'ऑनलाइन',
    'header.connected': 'कनेक्टेड',
    'header.setAiKey': 'एआई कुंजी सेट करें',
    'header.activeKey': 'सक्रिय',
    'header.theme': 'थीम',
    'header.language': 'भाषा',

    // Settings General
    'settings.title': 'सेटिंग्स',
    'settings.subtitle': 'अपने एआई कॉन्फ़िगरेशन, भाषा, खाते और प्राथमिकताओं को प्रबंधित करें',
    'settings.tabAi': 'एआई और एपीआई कुंजी',
    'settings.tabLanguage': 'भाषा / Language',
    'settings.tabAccount': 'खाता',
    'settings.tabNotifications': 'सूचनाएं',
    'settings.tabAppearance': 'दिखावट (थीम)',
    'settings.tabAbout': 'हमारे बारे में',

    // Settings - Language Tab
    'settings.langTitle': 'भाषा चयन / Language Choice',
    'settings.langDesc': 'अपनी पसंदीदा भाषा चुनें। चुनी गई भाषा संपूर्ण वेब एप्लिकेशन में लागू की जाएगी।',
    'settings.langSelectEn': 'English (अंग्रेज़ी)',
    'settings.langSelectEnSub': 'सभी इंटरफ़ेस, नेविगेशन और टूल के लिए अंग्रेज़ी भाषा।',
    'settings.langSelectHi': 'Hindi (हिंदी)',
    'settings.langSelectHiSub': 'संपूर्ण वेब ऐप में हिंदी भाषा का उपयोग करें।',
    'settings.langCurrentActive': 'वर्तमान में सक्रिय भाषा',
    'settings.langSuccessMsg': 'भाषा सफलतापूर्वक अपडेट की गई! संपूर्ण वेब ऐप अब इस भाषा में प्रदर्शित होगा:',
    'settings.langPreviewTitle': 'लाइव इंटरफ़ेस पूर्वावलोकन / Live Preview',
    'settings.langPreviewText': 'एआई करियर कोच में आपका स्वागत है! आपका व्यक्तिगत करियर मार्गदर्शन मंच।',

    // Settings - AI Tab
    'settings.aiTitle': 'एआई इंजन कॉन्फ़िगरेशन',
    'settings.aiDesc': 'अपना एआई प्रदाता चुनें और अपनी एपीआई कुंजी प्रबंधित करें। करियर कोच चैट, मॉक इंटरव्यू, रेज़्यूमे विश्लेषण और रोडमैप निर्माण के लिए उपयोग किया जाता है।',
    'settings.aiStatusActive': 'एआई सक्रिय है',
    'settings.aiStatusNoKey': 'कोई एपीआई कुंजी कॉन्फ़िगर नहीं है',
    'settings.aiProviderLabel': 'एआई प्रदाता',
    'settings.apiKeyLabel': 'एपीआई कुंजी',
    'settings.apiKeyPlaceholder': 'अपनी एपीआई कुंजी दर्ज करें',
    'settings.testKey': 'कुंजी का परीक्षण करें',
    'settings.saveKey': 'कुंजी सहेजें',
    'settings.clearKey': 'कुंजी हटाएं',
    'settings.keySavedSuccess': 'एपीआई कुंजी सहेजी गई और सभी एआई सुविधाओं के लिए सक्रिय की गई!',

    // Settings - Account Tab
    'settings.accountTitle': 'खाता विवरण',
    'settings.accountDesc': 'अपने खाते की साख और व्यक्तिगत प्रोफ़ाइल विवरण देखें।',
    'settings.fullName': 'पूरा नाम',
    'settings.emailAddress': 'ईमेल पता',
    'settings.accountStatus': 'खाता स्थिति',
    'settings.authentication': 'प्रमाणिकरण',
    'settings.statusActive': 'सक्रिय',
    'settings.signOutAccount': 'खाते से साइन आउट करें',

    // Settings - Notifications Tab
    'settings.notifTitle': 'सूचना प्राथमिकताएं',
    'settings.notifDesc': 'नियंत्रित करें कि आपको कौन सी गतिविधि सूचनाएं और अनुस्मारक प्राप्त होते हैं।',
    'settings.weeklyReport': 'साप्ताहिक प्रगति रिपोर्ट',
    'settings.weeklyReportSub': 'हर सप्ताह अपनी करियर प्रगति का सारांश प्राप्त करें',
    'settings.interviewReminder': 'साक्षात्कार अभ्यास अनुस्मारक',
    'settings.interviewReminderSub': 'नियमित रूप से मॉक इंटरव्यू का अभ्यास करने के लिए अनुस्मारक प्राप्त करें',
    'settings.roadmapProgress': 'रोडमैप मील के पत्थर अलर्ट',
    'settings.roadmapProgressSub': 'जब मैं रोडमैप मील के पत्थर पर पहुँचूँ तो मुझे सूचित करें',
    'settings.savePreferences': 'प्राथमिकताएं सहेजें',
    'settings.preferencesSaved': 'सहेजा गया!',

    // Settings - Appearance Tab
    'settings.appearanceTitle': 'दिखावट और थीम स्टूडियो',
    'settings.appearanceDesc': 'वास्तविक समय में प्लेटफॉर्म थीम, परिवेश चमक और रंग पैलेट को अनुकूलित करें।',
    'settings.resetDefaults': 'डिफ़ॉल्ट रीसेट करें',
    'settings.themePresets': 'थीम प्रीसेट (तत्काल लाइव स्विच)',
    'settings.accentColor': 'एक्सेंट कलर हाइलाइट',
    'settings.visualEffects': 'लेआउट और दृश्य प्रभाव',

    // Settings - About Tab
    'settings.aboutTitle': 'एआई करियर कोच के बारे में',
    'settings.aboutDesc': 'करियर विकास में तेजी लाने के लिए बनाया गया एक एआई-संचालित व्यक्तिगत करियर कोच और डिजिटल ट्विन ट्रैकिंग सिस्टम।',
    'settings.version': 'संस्करण',
    'settings.techStack': 'तकनीकी स्टैक',
    'settings.builtWith': 'Next.js, TypeScript, FastAPI और AI API के साथ निर्मित।',

    // Common Buttons & Labels
    'common.save': 'सहेजें',
    'common.saved': 'सहेजा गया!',
    'common.cancel': 'रद्द करें',
    'common.close': 'बंद करें',
    'common.loading': 'लोड हो रहा है...',
    'common.active': 'सक्रिय',
    'common.recommended': 'अनुशंसित',
    'common.view': 'देखें',
    'common.edit': 'संपादित करें',
    'common.delete': 'हटाएं',
    'common.back': 'वापस',
    'common.continue': 'जारी रखें',
    'common.start': 'शुरू करें',
    'common.status': 'स्थिति',
    'common.action': 'कार्रवाई',

    // Dashboard
    'dashboard.welcome': 'वापसी पर स्वागत है',
    'dashboard.subtitle': 'आपका एआई-संचालित करियर विकास कॉकपिट और डिजिटल ट्विन ट्रैकिंग',
    'dashboard.readinessScore': 'करियर तत्परता स्कोर',
    'dashboard.targetRole': 'लक्ष्य भूमिका',
    'dashboard.skillsMastered': 'कुशलताएं हासिल कीं',
    'dashboard.activeRoadmap': 'सक्रिय रोडमैप',
    'dashboard.quickActions': 'त्वरित कार्रवाई',
    'dashboard.startAssessment': 'मूल्यांकन शुरू करें',
    'dashboard.practiceInterview': 'मॉक इंटरव्यू अभ्यास करें',
    'dashboard.analyzeResume': 'रेज़्यूमे सुधारें',
    'dashboard.chatCoach': 'करियर कोच से बात करें',
    'dashboard.onboardingChecklist': 'ऑनबोर्डिंग चेकलिस्ट',

    // Assessment Page
    'assessment.title': 'इंटरएक्टिव करियर खोज मूल्यांकन',
    'assessment.questionStep': 'प्रश्न',
    'assessment.of': 'का',
    'assessment.instruction': 'कृपया वह विकल्प चुनें जो आपके स्वाभाविक दृष्टिकोण का सबसे अच्छा प्रतिनिधित्व करता है:',
    'assessment.nextBtn': 'अगला प्रश्न →',
    'assessment.submitBtn': 'मूल्यांकन पूरा करें और AI विश्लेषण प्राप्त करें ✨',
    'assessment.submitting': 'उत्तर सहेजा जा रहा है...',
    'assessment.loadingSession': 'करियर खोज सत्र लोड हो रहा है...',
    'assessment.analyzingTitle': 'आपकी करियर खोज प्रोफ़ाइल का विश्लेषण किया जा रहा है',
    'assessment.analyzingDesc': 'Gemini AI आपके समस्या निवारण, तार्किक तर्क और कार्यशैली की प्राथमिकताओं का हमारे 12 संरचित करियर ढांचे के विरुद्ध मूल्यांकन कर रहा है...',
    'assessment.resultsTitle': 'आपकी AI करियर खोज प्रोफ़ाइल',
    'assessment.resultsSubtitle': 'Gemini AI द्वारा संचालित साक्ष्य-आधारित करियर मूल्यांकन। आप अपने लक्ष्य करियर के चयन पर पूर्ण नियंत्रण बनाए रखते हैं।',
    'assessment.retake': 'मूल्यांकन पुनः दें',
    'assessment.archetypeLabel': 'करियर आर्किटाइप (प्रारूप)',
    'assessment.motivationLabel': 'प्रेरणा और चालक',
    'assessment.currentTarget': 'वर्तमान में चयनित लक्ष्य',
    'assessment.noneSelected': 'कोई चुना नहीं गया',
    'assessment.recommendedTitle': 'AI अनुशंसित करियर मैच',
    'assessment.setTarget': 'लक्ष्य भूमिका चुनें',
    'assessment.activeTarget': 'सक्रिय लक्ष्य',
    'assessment.exploreCompare': 'तुलना करें और जानें',
    'assessment.nextStepResume': 'अगला कदम: अपना रेज़्यूमे अपलोड करें और स्कैन करें',
    'assessment.uploadResumeBtn': 'रेज़्यूमे अपलोड करें →',

    // Modals
    'modal.apiKeyTitle': 'एआई एपीआई कुंजी कॉन्फ़िगर करें',
    'modal.apiKeyDesc': 'एआई कोचिंग सुविधाओं को सक्षम करने के लिए अपनी ग्रोक या गूगल जेमिनी एपीआई कुंजी जोड़ें।',
    'modal.themeTitle': 'थीम और दिखावट अनुकूलित करें',
    'modal.themeDesc': 'इंटरफ़ेस दृश्य थीम और एक्सेंट रंगों को अनुकूलित करें।',
  }
};

export function getTranslation(lang: Language, key: string, fallback?: string): string {
  const dict = translations[lang] || translations.en;
  if (dict && dict[key] !== undefined) {
    return dict[key];
  }
  const fallbackDict = translations.en;
  if (fallbackDict && fallbackDict[key] !== undefined) {
    return fallbackDict[key];
  }
  return fallback || key;
}
