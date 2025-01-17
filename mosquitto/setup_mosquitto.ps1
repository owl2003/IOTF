# Define the base directory as the current directory
$baseDir = $PWD.Path
$certsDir = "$baseDir\certs"
$brokerDir = "$certsDir\broker"
$caDir = "$certsDir\ca"
$configFile = "$baseDir\mosquitto.conf"
$toolsDir = "$baseDir\Tools"
$passwdDir = "$baseDir\passwd"
$passwdFile = "$passwdDir\passwd"

# Function to install mkcert (assumes mkcert.exe is already in the Tools directory)
function Install-Mkcert {
    Write-Host "Checking for mkcert in Tools directory..."
    if (-Not (Test-Path "$toolsDir\mkcert.exe")) {
        Write-Host "mkcert.exe not found in $toolsDir. Please download and place it in the Tools directory." -ForegroundColor Red
        exit 1
    }
    Write-Host "mkcert found in $toolsDir."

    # Add Tools directory to PATH
    $env:Path += ";$toolsDir"
    Write-Host "Tools directory added to PATH."

    # Install the local CA
    Write-Host "Installing the local CA..."
    & "$toolsDir\mkcert.exe" -install
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Local CA installed successfully."
    } else {
        Write-Host "Failed to install the local CA. Please check your setup." -ForegroundColor Red
        exit 1
    }
}

function Create-Directories {
    Write-Host "Creating directories..."
    New-Item -ItemType Directory -Path $certsDir -Force | Out-Null
    New-Item -ItemType Directory -Path $brokerDir -Force | Out-Null
    New-Item -ItemType Directory -Path $caDir -Force | Out-Null

    Write-Host "Directories created successfully"
}

# Function to generate certificates
function Generate-Certificates {
    Write-Host "Generating certificates..."
    Push-Location $brokerDir
    try {
        & "$toolsDir\mkcert.exe" localhost
        if (-Not (Test-Path "$brokerDir\localhost.pem")) {
            throw "Certificate generation failed. Check mkcert installation."
        }
        Write-Host "Certificates generated successfully."
    } catch {
        Write-Host "Error generating certificates: $_" -ForegroundColor Red
        exit 1
    }
    Pop-Location
}

# Function to copy the root CA certificate
function Copy-RootCA {
    Write-Host "Copying root CA certificate..."
    $rootCAPath = "$env:LocalAppData\mkcert\rootCA.pem"
    if (-Not (Test-Path $rootCAPath)) {
        Write-Host "Root CA certificate not found. Please ensure mkcert is installed correctly." -ForegroundColor Red
        exit 1
    }
    Copy-Item -Path $rootCAPath -Destination "$caDir\mkcertowl@kali.crt" -Force
    Write-Host "Root CA certificate copied successfully."
}



# Function to create the Mosquitto configuration file
function Create-ConfigFile {
    Write-Host "Creating mosquitto.conf..."
    $configContent = @"
# WebSocket listener on port 9001 with authentication
listener 9001
protocol websockets
allow_anonymous false

certfile $brokerDir\localhost.pem
keyfile $brokerDir\localhost-key.pem
cafile $caDir\mkcertowl@kali.crt
password_file $passwdFile

# MQTT listener on port 8883 with no authentication
listener 8883
protocol mqtt
allow_anonymous true
certfile $brokerDir\localhost.pem
keyfile $brokerDir\localhost-key.pem
cafile $caDir\mkcertowl@kali.crt
tls_version tlsv1.2
"@
    Set-Content -Path $configFile -Value $configContent
    Write-Host "mosquitto.conf created successfully."
}

# Main script execution
Write-Host "Starting Mosquitto setup..."

# Install mkcert (assumes mkcert.exe is already in the Tools directory)
Install-Mkcert

# Create directories
Create-Directories

# Generate certificates
Generate-Certificates

# Copy the root CA certificate
Copy-RootCA


# Create the Mosquitto configuration file
Create-ConfigFile

Write-Host "Setup completed successfully!"
Write-Host "Mosquitto configuration file: $configFile"
Write-Host "Certificates are located in: $certsDir"
Write-Host "Password file is located in: $passwdFile"