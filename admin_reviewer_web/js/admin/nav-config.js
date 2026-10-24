(function (global) {
  global.FacultyLinkAdminNav = [
    {
      section: 'Overview',
      items: [{ id: 'dashboard', label: 'Dashboard', href: 'dashboard.html', icon: 'layout-dashboard' }],
    },
    {
      section: 'People',
      items: [
        { id: 'faculty', label: 'Faculty Management', href: 'faculty.html', icon: 'users' },
        { id: 'reviewers', label: 'Reviewer Management', href: 'reviewers.html', icon: 'user-check' },
      ],
    },
    {
      section: 'Configuration',
      items: [
        { id: 'evaluation-schedule', label: 'Evaluation Schedule', href: 'evaluation-schedule.html', icon: 'calendar-days' },
        { id: 'kra-config', label: 'KRA Configuration', href: 'kra-config.html', icon: 'sliders-horizontal' },
        { id: 'scoring-config', label: 'Validation & Scoring', href: 'scoring-config.html', icon: 'clipboard-check' },
      ],
    },
    {
      section: 'Monitoring',
      items: [
        { id: 'documents', label: 'Document Monitoring', href: 'documents.html', icon: 'file-search' },
        { id: 'rank-simulation', label: 'Rank Simulation', href: 'rank-simulation.html', icon: 'chart-no-axes-combined' },
      ],
    },
    {
      section: 'System',
      items: [
        { id: 'reports', label: 'Reports & Analytics', href: 'reports.html', icon: 'chart-column-increasing' },
        { id: 'notifications', label: 'Notifications', href: 'notifications.html', icon: 'bell' },
        { id: 'settings', label: 'Account Settings', href: 'settings.html', icon: 'settings' },
      ],
    },
  ]
})(window)
