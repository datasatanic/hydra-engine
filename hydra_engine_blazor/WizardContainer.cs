using System.Net.Http.Json;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace hydra_engine_blazor;

public class WizardContainer
{
    public event Action? OnChange;
    private void NotifyStateChanged() => OnChange?.Invoke();
    private readonly HttpClient _client;
    private JsonSerializerOptions options = new()
    {
        Converters =
        {
            new JsonStringEnumConverter()
        },
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
    };
    public WizardContainer(IHttpClientFactory ClientFactory)
    {
        _client = ClientFactory.CreateClient("WebApi");
    }
    public async Task<object?> GetTree()
    {
        return await _client.GetFromJsonAsync<object>($"api/wizard/tree");
    }
    public async Task<object?> GetFormInfo(string url)
    {
        return await _client.GetFromJsonAsync<object>($"api/wizard/tree/{url}");
    }
}