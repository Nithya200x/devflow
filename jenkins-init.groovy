import jenkins.model.*
import hudson.security.*
import hudson.model.*

def instance = Jenkins.getInstance()

// Set security realm
def realm = new HudsonPrivateSecurityRealm(false, false, null)
realm.createAccount("admin", "admin123")
instance.setSecurityRealm(realm)

// Set authorization - full access once logged in
def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(true)
instance.setAuthorizationStrategy(strategy)

instance.setCrumbIssuer(null)

instance.save()

println "=== Jenkins init complete ==="
println "Admin: admin / admin123"
println "Anonymous read: true"
println "CSRF: disabled"
