// lxc_manager.groovy
import groovy.json.JsonSlurper

// Internal storage for environment variables
def envVars = [:]

def set_environment(String apiUrl, String token, String containerName, String key, String value) {
    echo "Staging env var: ${key}=${value}"
    envVars[key] = value
}

def get_next_vmid(String apiUrl, String token) {
    echo "Querying for next available VMID..."

    // We use /api2/json/cluster/nextid for easier parsing in Groovy
    def response = httpRequest httpMode: 'GET',
                                url: "${apiUrl}/cluster/nextid",
                                customHeaders: [[name: 'Authorization', value: "PVEAPIToken=${token}"]]

    def json = new JsonSlurper().parseText(response.content)

    return json.data
}

def create(String apiUrl, String token, String containerName, List<String> targetTags, String node = "pve") {
    echo "Creating container: ${containerName}"

    def vmid = get_next_vmid(apiUrl, token)
    def createParams = "vmid=${vmid}&hostname=${containerName}&ostemplate=local:vztmpl/ubuntu-22.04-standard.tar.zst&net0=name=eth0,bridge=vmbr0,ip=dhcp&tags=${targetTags.join(';')}"

    // 1. Create the LXC (Adjust payload based on your specific Proxmox API setup)
    httpRequest httpMode: 'POST',
                url: "${apiUrl}/api2/json/nodes/${node}/lxc",
                contentType: 'APPLICATION_FORM_URLENCODED',
                customHeaders: [[name: 'Authorization', value: "PVEAPIToken=${token}"]],
                requestBody: createParams

    // 2. Wait for container to exist, then write the .env file
    // We use 'pct exec' via the API or SSH to create the file
    def envFileContent = envVars.collect { k, v -> "${k}=${v}" }.join('\n')

    def execCommand = "command=bash -c \"echo -e '${envFileContent}' > /var/www/project/.env\""

    echo "Injecting environment variables into .env..."
    // Using Proxmox API to write the file directly inside the container
    httpRequest httpMode: 'POST',
                url: "${apiUrl}/api2/json/nodes/${node}/lxc/${vmid}/exec",
                contentType: 'APPLICATION_FORM_URLENCODED',
                customHeaders: [[name: 'Authorization', value: "PVEAPIToken=${token}"]],
                requestBody: execCommand
}

def get_vmids_by_tags(String apiUrl, String token, List<String> targetTags) {
    // Proxmox API Endpoint for cluster resources
    def endpoint = "${apiUrl}/api2/json/cluster/resources?type=vm"

    // Setup the connection
    def connection = new URL(endpoint).openConnection()
    connection.setRequestMethod("GET")
    connection.setRequestProperty("Authorization", "PVEAPIToken=${token}")
    connection.setRequestProperty("Accept", "application/json")

    if (connection.responseCode != 200) {
        throw new Exception("API Request Failed: ${connection.responseCode} - ${connection.errorStream.text}")
    }

    def response = new JsonSlurper().parseText(connection.inputStream.text)
    def foundVmids = []

    response.data.each { resource ->
        // Proxmox tags are returned as a semicolon-separated string (e.g., "web;prod;linux")
        if (resource.tags) {
            def resourceTagList = resource.tags.split(';')

            // Check if ALL target tags are present on this resource
            if (resourceTagList.containsAll(targetTags)) {
                foundVmids << resource.vmid
            }
        }
    }

    return foundVmids
}

def get_old_vmids(String apiUrl, String token, String projectName, String currentHash) {
    // Proxmox API Endpoint for cluster resources
    def endpoint = "${apiUrl}/api2/json/cluster/resources?type=vm"

    // Setup the connection
    def connection = new URL(endpoint).openConnection()
    connection.setRequestMethod("GET")
    connection.setRequestProperty("Authorization", "PVEAPIToken=${token}")
    connection.setRequestProperty("Accept", "application/json")

    if (connection.responseCode != 200) {
        throw new Exception("API Request Failed: ${connection.responseCode} - ${connection.errorStream.text}")
    }

    def response = new JsonSlurper().parseText(connection.inputStream.text)
    def oldVmids = []

    response.data.each { resource ->
        if (resource.tags) {
            def tags = resource.tags.split(';')

            // LOGIC: If it belongs to the project, but the hash is DIFFERENT
            if (tags.contains(projectName) && !tags.contains(currentHash)) {
                oldVmids << resource.vmid
            }
        }
    }

    return oldVmids
}

return this