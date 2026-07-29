# Per-repo fleet start config for dark-app-factory
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'dark-app-factory'
    BackendPort  = 10738
    FrontendPort = 10740
    HealthPath   = '/api/v1/health'
    WebRoot      = 'D:\Dev\repos\dark-app-factory\web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'web.server:app'
        Env           = @{ PORT = '10738' }
        WorkDir       = 'D:\Dev\repos\dark-app-factory'
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'bun'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
