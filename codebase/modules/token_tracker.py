"""
TOKEN TRACKER - Control de consumo de tokens y costos estimados

Centraliza el registro de todos los tokens consumidos por OpenAI y Google Gemini.
Guarda un log acumulativo en /logs/token_usage.json para control histórico.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# ── Precios aproximados por 1M tokens (USD) ──────────────────────────────────
# Actualizar si cambian los precios en la web de OpenAI / Google
PRICING = {
    # OpenAI
    "gpt-4o": {
        "input":  2.50,   # USD por 1M tokens de entrada
        "output": 10.00,  # USD por 1M tokens de salida
    },
    "gpt-4": {
        "input":  30.00,
        "output": 60.00,
    },
    "gpt-4-turbo": {
        "input":  10.00,
        "output": 30.00,
    },
    "gpt-3.5-turbo": {
        "input":  0.50,
        "output": 1.50,
    },
    # Google Gemini (aproximados)
    "gemini-2.5-flash-image": {
        "input":  0.0,    # Imagen generada = precio por imagen, no por token
        "output": 0.0,
    },
    "imagen-4.0-fast-generate-001": {
        "input":  0.0,
        "output": 0.0,
        "per_image": 0.04,  # USD por imagen generada
    },
}


class TokenTracker:
    """
    Singleton para registrar y acumular el uso de tokens en toda la sesión.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.session_start = datetime.now().isoformat()
        self.entries: list[dict] = []
        self.totals = {
            "prompt_tokens":     0,
            "completion_tokens": 0,
            "total_tokens":      0,
            "images_generated":  0,
            "estimated_cost_usd": 0.0,
        }
        self._log_path: Optional[Path] = None

    def set_log_path(self, logs_dir: Path):
        """Configura la ruta del archivo de log."""
        logs_dir.mkdir(parents=True, exist_ok=True)
        self._log_path = logs_dir / "token_usage.json"

    # ── Registro de tokens ────────────────────────────────────────────────────

    def register_openai(
        self,
        operation: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Registra el uso de tokens de una llamada a OpenAI.

        Args:
            operation:         Nombre descriptivo (p.ej. "generar_historia")
            model:             Modelo usado (p.ej. "gpt-4o")
            prompt_tokens:     Tokens de entrada
            completion_tokens: Tokens de salida
            total_tokens:      Total
            metadata:          Datos extra opcionales (titulo, elementos, etc.)

        Returns:
            dict con el resumen del registro incluyendo costo estimado
        """
        cost = self._calc_cost_llm(model, prompt_tokens, completion_tokens)

        entry = {
            "timestamp":         datetime.now().isoformat(),
            "provider":          "openai",
            "operation":         operation,
            "model":             model,
            "prompt_tokens":     prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens":      total_tokens,
            "estimated_cost_usd": round(cost, 6),
            "metadata":          metadata or {},
        }

        self.entries.append(entry)
        self.totals["prompt_tokens"]     += prompt_tokens
        self.totals["completion_tokens"] += completion_tokens
        self.totals["total_tokens"]      += total_tokens
        self.totals["estimated_cost_usd"] = round(
            self.totals["estimated_cost_usd"] + cost, 6
        )

        self._save_log()
        return entry

    def register_image(
        self,
        operation: str,
        model: str,
        images_count: int = 1,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Registra generación de imágenes (Gemini/Imagen).

        Args:
            operation:    Nombre descriptivo
            model:        Modelo de imagen usado
            images_count: Número de imágenes generadas
            metadata:     Datos extra opcionales
        """
        price_info = PRICING.get(model, {})
        cost = price_info.get("per_image", 0.04) * images_count

        entry = {
            "timestamp":         datetime.now().isoformat(),
            "provider":          "google",
            "operation":         operation,
            "model":             model,
            "images_generated":  images_count,
            "estimated_cost_usd": round(cost, 6),
            "metadata":          metadata or {},
        }

        self.entries.append(entry)
        self.totals["images_generated"]  += images_count
        self.totals["estimated_cost_usd"] = round(
            self.totals["estimated_cost_usd"] + cost, 6
        )

        self._save_log()
        return entry

    # ── Reportes ──────────────────────────────────────────────────────────────

    def get_session_summary(self) -> dict:
        """Devuelve un resumen de la sesión actual."""
        return {
            "session_start":     self.session_start,
            "session_end":       datetime.now().isoformat(),
            "total_calls":       len(self.entries),
            **self.totals,
        }

    def print_summary(self, label: str = "SESIÓN"):
        """Imprime un resumen formateado en consola."""
        s = self.totals
        print(f"\n{'─'*55}")
        print(f"  📊 CONSUMO DE TOKENS — {label}")
        print(f"{'─'*55}")
        print(f"  Tokens de entrada  (prompt):     {s['prompt_tokens']:>10,}")
        print(f"  Tokens de salida   (completion): {s['completion_tokens']:>10,}")
        print(f"  ────────────────────────────────────────────────")
        print(f"  TOTAL TOKENS:                    {s['total_tokens']:>10,}")
        if s['images_generated'] > 0:
            print(f"  Imágenes generadas:              {s['images_generated']:>10,}")
        print(f"  Costo estimado:                  ${s['estimated_cost_usd']:>10.4f} USD")
        print(f"{'─'*55}\n")

    def print_entry(self, entry: dict):
        """Imprime un registro individual de forma compacta."""
        op  = entry.get("operation", "?")
        mod = entry.get("model", "?")
        if "total_tokens" in entry:
            tok = entry["total_tokens"]
            cost = entry["estimated_cost_usd"]
            print(f"  🔢 [{op}] {mod} → {tok:,} tokens (~${cost:.4f} USD)")
        elif "images_generated" in entry:
            imgs = entry["images_generated"]
            cost = entry["estimated_cost_usd"]
            print(f"  🖼️  [{op}] {mod} → {imgs} imagen(es) (~${cost:.4f} USD)")

    # ── Persistencia ──────────────────────────────────────────────────────────

    def _save_log(self):
        """Guarda el log acumulativo en disco."""
        if self._log_path is None:
            return
        try:
            # Cargar histórico existente
            if self._log_path.exists():
                with open(self._log_path, "r", encoding="utf-8") as f:
                    historical = json.load(f)
            else:
                historical = {"sessions": []}

            # Actualizar sesión actual (o añadirla si es nueva)
            session_data = {
                "session_start": self.session_start,
                "session_end":   datetime.now().isoformat(),
                "totals":        self.totals,
                "entries":       self.entries,
            }

            # Reemplazar sesión si ya existe, si no añadir
            sessions = historical.get("sessions", [])
            idx = next(
                (i for i, s in enumerate(sessions)
                 if s.get("session_start") == self.session_start),
                None,
            )
            if idx is not None:
                sessions[idx] = session_data
            else:
                sessions.append(session_data)

            historical["sessions"] = sessions
            historical["last_updated"] = datetime.now().isoformat()

            # Totales históricos acumulados
            all_tokens  = sum(s["totals"].get("total_tokens", 0) for s in sessions)
            all_images  = sum(s["totals"].get("images_generated", 0) for s in sessions)
            all_cost    = sum(s["totals"].get("estimated_cost_usd", 0.0) for s in sessions)
            historical["cumulative"] = {
                "total_tokens":       all_tokens,
                "images_generated":   all_images,
                "estimated_cost_usd": round(all_cost, 4),
                "total_sessions":     len(sessions),
            }

            with open(self._log_path, "w", encoding="utf-8") as f:
                json.dump(historical, f, indent=2, ensure_ascii=False)

        except Exception as e:
            # No interrumpir el flujo principal por un error de log
            print(f"  ⚠️  No se pudo guardar el log de tokens: {e}")

    # ── Utilidades ────────────────────────────────────────────────────────────

    def _calc_cost_llm(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calcula el costo estimado para un modelo LLM."""
        price = PRICING.get(model, {"input": 0.0, "output": 0.0})
        cost = (prompt_tokens / 1_000_000) * price["input"]
        cost += (completion_tokens / 1_000_000) * price["output"]
        return cost


# Instancia global (singleton)
tracker = TokenTracker()
