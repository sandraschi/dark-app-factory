# Per-repo fleet start config for dark-app-factory
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'dark-app-factory'
    BackendPort  = 10739
    FrontendPort = 10738
    HealthPath   = '/api/v1/health'
    WebRoot      = 'D:\Dev\repos\dark-app-factory\web'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'server:app'
        Env           = @{ WEB_PORT = '10739' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
