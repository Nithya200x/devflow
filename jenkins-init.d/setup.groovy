import jenkins.model.*
import hudson.security.*
import hudson.model.*

def instance = Jenkins.getInstance()

def realm = new HudsonPrivateSecurityRealm(false, false, null)
realm.createAccount("admin", "admin123")
instance.setSecurityRealm(realm)

def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(true)
instance.setAuthorizationStrategy(strategy)

instance.setCrumbIssuer(null)
instance.save()

println "=== Jenkins init complete: admin/admin123 ==="
