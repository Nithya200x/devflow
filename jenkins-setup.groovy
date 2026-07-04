import jenkins.model.*
import hudson.security.*
import hudson.model.*

def instance = Jenkins.getInstance()

// Set security realm
def realm = new HudsonPrivateSecurityRealm(false, false, null)
realm.createAccount("admin", "admin123")
instance.setSecurityRealm(realm)

// Set authorization strategy
def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

// Add admin user email property
def user = User.get("admin", false)
if (user != null) {
    def mailer = new hudson.tasks.Mailer.UserProperty("admin@devflow.local")
    user.addProperty(mailer)
    user.save()
}

instance.save()
println("Jenkins setup complete: admin / admin123")
