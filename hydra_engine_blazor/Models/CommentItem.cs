using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace hydra_engine_blazor.Models;

public class CommentItem
{
    [DataMember(Name = "url", EmitDefaultValue = false)]
    [JsonPropertyName("url")]
    public string Url { get; set; }
    [DataMember(Name = "file_id", EmitDefaultValue = false)]
    [JsonPropertyName("file_id")]
    public string FileId { get; set; }
    [DataMember(Name = "is_comment", EmitDefaultValue = false)]
    [JsonPropertyName("is_comment")]
    public bool IsComment { get; set; }
}