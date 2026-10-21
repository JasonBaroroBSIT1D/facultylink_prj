(function (global) {
  global.FacultyLinkAdminNav = [
    { section: 'Overview', items: [{ id: 'dashboard', label: 'Dashboard', href: 'dashboard.html' }] },
    {
      section: 'People',
      items: [
        { id: 'faculty', label: 'Faculty Management', href: 'faculty.html' },
        { id: 'reviewers', label: 'Reviewer Management', href: 'reviewers.html' },
      ],
    },
    {
      section: 'Configuration',
      items: [
        { id: 'evaluation-schedule', label: 'Evaluation Schedule', href: 'evaluation-schedule.html' },
        { id: 'kra-config', label: 'KRA Configuration', href: 'kra-config.html' },
        { id: 'scoring-config', label: 'Validation & Scoring', href: 'scoring-config.html' },
      ],
    },
    {
      section: 'Monitoring',
      items: [
        { id: 'documents', label: 'Document Monitoring', href: 'documents.html' },
        { id: 'rank-simulation', label: 'Rank Simulation', href: 'rank-simulation.html' },
      ],
    },
    {
      section: 'System',
      items: [
        { id: 'reports', label: 'Reports & Analytics', href: 'reports.html' },
        { id: 'notifications', label: 'Notifications', href: 'notifications.html' },
        { id: 'settings', label: 'Account Settings', href: 'settings.html' },
      ],
    },
  ]
})(window)
