﻿using System.Net.Http.Json;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Serialization;
using hydra_engine_blazor.Models;

namespace hydra_engine_blazor;

public class WizardContainer
{
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
    public async Task<HttpResponseMessage> CheckCondition(string path, IEnumerable<Condition> condition)
    {
        var json = JsonSerializer.Serialize(condition, options);
        HttpContent content = new StringContent(json, Encoding.UTF8, "application/json");
        return await _client.PostAsync($"api/wizard/form/condition?path={path}",content);
    }

    public async Task<HttpResponseMessage> InitArch(string archName)
    {
        HttpContent content = new StringContent("", Encoding.UTF8, "application/json");
        return await _client.PostAsync($"api/wizard/init_arch?name={archName}",content);
    }

    public async Task<HttpResponseMessage> DeploySite(string siteName)
    {
        HttpContent content = new StringContent("", Encoding.UTF8, "application/json");
        return await _client.PostAsync($"api/wizard/deploy?name={siteName}",content);
    }
}
