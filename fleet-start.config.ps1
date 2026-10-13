# Per-repo fleet start config for dark-app-factory
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'dark-app-factory'
    BackendPort  = 10739
    FrontendPort = 10738
    HealthPath   = '/api/v1/health'
    WebRoot      = 'web'
    Backend = @{
        Kind          = 'uvicorn-web-app'
        UvicornTarget = 'server:app'
        WorkDir       = 'web'
        SyncExtras    = @('dev')
        SyncOnStart  = $true
        Env           = @{ WEB_PORT = '10739' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
