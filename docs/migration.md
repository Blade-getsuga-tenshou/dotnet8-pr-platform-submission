# Migration: Azure Pipeline to GitHub Actions

Source: case-study-ado-pipeline.yaml from the case study zip. Each row shows what happened to that step.

| Azure Pipeline step | GitHub Actions result | Status |
|---|---|---|
| trigger none with pr branches main, drafts false | on: pull_request into main, skipped for drafts | Converted |
| pool vmImage windows-latest | runs-on: windows-latest | Converted |
| Variables solution, buildConfiguration | Workflow env and reusable workflow inputs | Converted |
| Variable buildPlatform x86 | Sample builds and tests for x86 in the x86 job on a hosted runner | Converted (non-required job) |
| PowerShell: install .NET 8 SDK x86 with dotnet-install.ps1 | actions/setup-dotnet with 8.0.x and architecture x86 in the x86 job | Replaced |
| PowerShell: install VC++ x86 redistributable | Removed. The sample does not need it on hosted runners | Removed. Verify on legacy products |
| NuGetToolInstaller | Removed. The .NET SDK includes NuGet | Removed |
| NuGetCommand restore with nuget.config | dotnet restore. No nuget.config was supplied, so restore uses the default feed | Replaced |
| VSBuild build (x86, Release) | dotnet build --configuration Release | Replaced |
| VSBuild "Publish artifacts" | dotnet publish of src/Core, uploaded as build-output | Replaced; the original built twice |
| PowerShell: set DOTNET_ROOT for x86 | Removed. setup-dotnet manages the install path | Removed |
| VSTest with coverlet.runsettings, x86 | dotnet test with XPlat Code Coverage, uploaded as test-results | Replaced; custom runsettings not carried over |

## Gaps to know about

- coverlet.runsettings and nuget.config were referenced but not supplied. The conversion uses default coverage and default NuGet feeds. If the legacy settings include coverage thresholds or private feeds, they need to be supplied and reapplied.
- The sample code is a template. It validates the pipeline pattern, not the legacy product's test suite.
- Legacy products with 32-bit-only dependencies (for example certain COM objects, drivers, or native libraries) are not covered by the sample. They need the self-hosted 32-bit runner path in governance.md.