import { app } from "../../../scripts/app.js";

const EXTENSION_NAME = "Dapao.RHApp.DynamicParameters.v10";

setTimeout(async () => {
    const loaded = (app.extensions || []).some((extension) => extension.name === EXTENSION_NAME);
    if (loaded) return;

    try {
        await import("./dapao_rh_app_ui.js?v=20260719-10");
        console.info("[Dapao RH App] Loaded widget-bound smart inputs UI v10 with cache bypass.");
    } catch (error) {
        console.error("[Dapao RH App] Failed to load widget-bound smart inputs UI v10:", error);
    }
}, 650);
