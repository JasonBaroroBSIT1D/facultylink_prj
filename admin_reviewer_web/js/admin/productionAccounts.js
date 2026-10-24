/**
 * Development seed accounts bundled in facultylink_complete_schema.sql.
 * Hidden from Faculty / Reviewer Management until removed from PostgreSQL (admin approval).
 */
window.FacultyLinkAdminProductionAccounts = {
  DEMO_SEED_EMAILS: ['faculty@facultylink.edu', 'reviewer@facultylink.edu'],

  isDemoSeedEmail: function (email) {
    var normalized = String(email || '').trim().toLowerCase()
    return this.DEMO_SEED_EMAILS.indexOf(normalized) >= 0
  },

  excludeDemoSeedAccounts: function (users) {
    var self = this
    return (users || []).filter(function (u) {
      return !self.isDemoSeedEmail(u.email)
    })
  },
}
