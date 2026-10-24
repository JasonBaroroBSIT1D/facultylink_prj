/**
 * Legacy setup-password links are retired. New accounts use email temporary passwords + login.
 */
document.addEventListener('DOMContentLoaded', function () {
  var params = new URLSearchParams(window.location.search)
  if (params.has('token')) {
    params.delete('token')
  }
  params.set('notice', 'use-temp-password')
  window.location.replace('login.html?' + params.toString())
})
