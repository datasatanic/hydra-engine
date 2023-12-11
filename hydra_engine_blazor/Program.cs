using Blazored.Toast;
using Microsoft.AspNetCore.Components.Web;
using Microsoft.AspNetCore.Components.WebAssembly.Hosting;
using hydra_engine_blazor;

var builder = WebAssemblyHostBuilder.CreateDefault(args);
builder.RootComponents.Add<App>("#app");
builder.RootComponents.Add<HeadOutlet>("head::after");

builder.Services.AddScoped(sp => new HttpClient { BaseAddress = new Uri(builder.HostEnvironment.BaseAddress) });
builder.Services
    .AddHttpClient("WebApi",
        client => client.BaseAddress = new Uri(builder.Configuration.GetConnectionString("WebApi")));


builder.Services.AddSingleton<SettingsContainer>();
builder.Services.AddSingleton<WizardContainer>();
builder.Services.AddBlazoredToast();
await builder.Build().RunAsync();