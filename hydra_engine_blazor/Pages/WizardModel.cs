using hydra_engine_blazor.Models;

namespace DefaultNamespace;

public class WizardModel
{
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
    private bool isExpandAll;

    public bool IsExpandAll
    {
        get => isExpandAll;
        set
        {
            isExpandAll = value;
            NotifyStateChanged();
        }
    }
    public event Action? OnChange;
    public void NotifyStateChanged() => OnChange?.Invoke();
}