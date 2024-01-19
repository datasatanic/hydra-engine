using hydra_engine_blazor.Models;

namespace DefaultNamespace;

public class WizardModel
{
    private string title;

    public string Title
    {
        get => title;
        set
        {
            title = value;
            NotifyStateChanged();
        }
    }

    private ControlsMeta controlsMeta;

    public ControlsMeta ControlsMeta
    {
        get => controlsMeta;
        set
        {
            controlsMeta = value;
            NotifyStateChanged();
        }
    }
    public event Action? OnChange;
    private void NotifyStateChanged() => OnChange?.Invoke();
}