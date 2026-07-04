import jenkins.model.*
def inst = Jenkins.instance
def jlc = inst.getDescriptor('jenkins.model.JenkinsLocationConfiguration')
jlc.setUrl('http://localhost:8080')
jlc.save()
inst.save()
println 'URL configured'
