(function (global) {
  global.FacultyLinkReviewerNav = [
    {
      section: 'Review',
      items: [
        { id: 'dashboard', label: 'Dashboard', href: 'dashboard.html', icon: 'layout-dashboard' },
        { id: 'evaluation-schedule', label: 'Evaluation Schedule', href: 'evaluation-schedule.html', icon: 'calendar-days' },
      ],
    },
    {
      section: 'Faculty',
      items: [
        { id: 'assigned-faculty', label: 'Assigned Faculty', href: 'assigned-faculty.html', icon: 'users' },
        { id: 'document-review', label: 'Document Review', href: 'document-review.html', icon: 'file-text' },
        { id: 'kra-assessment', label: 'KRA Assessment', href: 'kra-assessment.html', icon: 'clipboard-check' },
      ],
    },
    {
      section: 'Outcomes',
      items: [
        { id: 'rank-simulation', label: 'Rank Simulation Review', href: 'rank-simulation.html', icon: 'chart-no-axes-combined' },
        { id: 'evaluation-history', label: 'Evaluation History', href: 'evaluation-history.html', icon: 'history' },
      ],
    },
    {
      section: 'Account',
      items: [
        { id: 'notifications', label: 'Notifications', href: 'notifications.html', icon: 'bell' },
        { id: 'settings', label: 'Account Settings', href: 'settings.html', icon: 'settings' },
      ],
    },
  ]
})(window)
