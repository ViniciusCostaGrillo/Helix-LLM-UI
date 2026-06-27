import json
import os
from backend.schemas.analyzer import AnalysisResult
from backend.schemas.codegen import CodegenResult, GeneratedComponent
from backend.schemas.extractor import ExtractionResult
from backend.utils.custom_logger import setup_logger

logger = setup_logger("codegen.code_generator")


class CodeGenerator:
    """Service to convert parsed HTML structures, visual rules, and layout analyses

    into React components using Tailwind CSS, falling back to mock templates when keys are inactive.
    """

    def generate(
        self, extraction: ExtractionResult, analysis: AnalysisResult
    ) -> CodegenResult:
        logger.info("Initializing React/Tailwind code generation...")

        # 1. Select provider based on environment variables
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        # Skip placeholders
        if gemini_key == "your_gemini_api_key_here":
            gemini_key = None
        if openai_key == "your_openai_api_key_here":
            openai_key = None
        if anthropic_key == "your_anthropic_api_key_here":
            anthropic_key = None

        prompt = self._build_prompt(extraction, analysis)

        # 2. Execute LLM call or fallback
        if gemini_key:
            logger.info("Using Google Gemini provider for code generation...")
            return self._call_gemini(prompt, gemini_key)
        elif openai_key:
            logger.info("Using OpenAI GPT provider for code generation...")
            return self._call_openai(prompt, openai_key)
        elif anthropic_key:
            logger.info("Using Anthropic Claude provider for code generation...")
            return self._call_anthropic(prompt, anthropic_key)
        else:
            logger.warning(
                "No LLM API keys configured. Falling back to dynamic Mock Code Generator."
            )
            return self._run_mock_codegen(analysis)

    def _build_prompt(self, extraction: ExtractionResult, analysis: AnalysisResult) -> str:
        """Assembles a code-generation prompt containing analysis design tokens and component details."""
        components_specs = []
        for idx, comp in enumerate(analysis.components):
            components_specs.append(
                f"Component {idx+1}:\n"
                f"- ID: {comp.component_id}\n"
                f"- Type: {comp.type}\n"
                f"- Description: {comp.description}\n"
                f"- Layout Flow: {comp.layout_type}\n"
                f"- Text blocks inside: {comp.text_content}\n"
                f"- Extracted Classes: {comp.style_classes}"
            )
        comp_str = "\n\n".join(components_specs)

        prompt = f"""You are a principal frontend engineer specializing in React, TypeScript, and Tailwind CSS.
Convert the following analyzed layout, design tokens, and components guide into clean, self-contained, modular, and responsive React functional components.

--- DESIGN SYSTEM TOKENS ---
Primary Brand Color: {analysis.theme.primary_color}
Secondary Accent Color: {analysis.theme.secondary_color}
Page Canvas Background Color: {analysis.theme.background_color}
Text Font Family Stack: {analysis.theme.fonts}
Primary Text Color: {analysis.theme.text_color}

--- VISUAL AND SEMANTIC COMPONENT SPECS ---
{comp_str}

--- LAYOUT GUIDELINES & RECOMMENDATIONS ---
Spacing Flow: {analysis.layout.spacing_feel}
Responsiveness: {analysis.layout.responsiveness}
AI Layout Recommendations: {analysis.ai_recommendations}

--- CODE GENERATION REQUIREMENTS ---
- You must generate a structured JSON document mapping to the CodegenResult model.
- For each UI component, output a corresponding React functional component inside the `components` list.
- Component names must use PascalCase (e.g. Header, HeroSection).
- Code blocks must contain complete, importable React TSX files using inline Tailwind CSS utility classes.
- Ensure all styling aligns with the design tokens.
"""
        return prompt

    def _call_gemini(self, prompt: str, api_key: str) -> CodegenResult:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro")
        model = genai.GenerativeModel(model_name)
        
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=CodegenResult,
                ),
            )
            data = json.loads(response.text)
            return CodegenResult(**data)
        except Exception as e:
            logger.error(f"Gemini API code generation failed: {e}")
            raise

    def _call_openai(self, prompt: str, api_key: str) -> CodegenResult:
        from openai import OpenAI
        import json

        base_url = os.getenv("OPENAI_API_BASE")
        model = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
        client = OpenAI(api_key=api_key, base_url=base_url)
        try:
            if "gpt-4o" in model:
                response = client.beta.chat.completions.parse(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a code generator that produces clean React + Tailwind component files.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    response_format=CodegenResult,
                )
                parsed_result = response.choices[0].message.parsed
            else:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a code generator that produces clean React + Tailwind component files. Output JSON matching the CodegenResult schema.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                )
                raw_content = response.choices[0].message.content
                if not raw_content:
                    raise ValueError("Received empty response from local model.")
                parsed_result = CodegenResult(**json.loads(raw_content))

            if not parsed_result:
                raise ValueError("OpenAI parse returned empty code payload.")
            return parsed_result
        except Exception as e:
            logger.error(f"OpenAI API code generation failed: {e}")
            raise

    def _call_anthropic(self, prompt: str, api_key: str) -> CodegenResult:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)
        schema_info = json.dumps(CodegenResult.model_json_schema(), indent=2)
        system_instructions = (
            "You are a code generation assistant. You must output ONLY valid JSON matching this schema:\n"
            f"{schema_info}\nDo not wrap the response in markdown blocks or output introductory chat text."
        )

        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=4000,
                system=system_instructions,
                messages=[{"role": "user", "content": prompt}],
            )
            content_text = "".join([block.text for block in message.content])
            data = json.loads(content_text)
            return CodegenResult(**data)
        except Exception as e:
            logger.error(f"Anthropic API code generation failed: {e}")
            raise

    def _run_mock_codegen(self, analysis: AnalysisResult) -> CodegenResult:
        """Dynamic code builder generating actual React component code text from layout models."""
        components = []
        theme = analysis.theme
        
        # Avoid f-string double-bracing issues for Javascript output
        o_brace = "{"
        c_brace = "}"
        dollar = "$"

        # Generate individual components based on their type
        for comp in analysis.components:
            # Determine PascalCase name
            comp_name = comp.type.capitalize()
            if not comp_name.endswith("Section") and comp_name not in ("Header", "Footer"):
                comp_name += "Section"
            if len(components) > 0 and comp_name == components[0].name:
                comp_name = f"{comp_name}CardGrid"

            # Create clean label lines
            content_html = ""
            for text in comp.text_content:
                if text.strip() == "Example Domain":
                    content_html += f'        <h1 className="text-3xl font-extrabold tracking-tight mb-4">{text}</h1>\n'
                else:
                    content_html += f'        <p className="text-base text-opacity-90 max-w-2xl mb-4 leading-relaxed">{text}</p>\n'

            # Construct layout styles
            classes_str = " ".join(comp.style_classes)
            font_stack = theme.fonts[0] if theme.fonts else 'sans'

            # Generate React Code block
            code = f"""import React from 'react';

interface {comp_name}Props {o_brace}
  className?: string;
{c_brace}

export default function {comp_name}({o_brace} className = '' {c_brace}: {comp_name}Props) {o_brace}
  return (
    <section 
      className={o_brace}`w-full py-12 px-6 flex flex-col items-center justify-center text-center font-{font_stack} border-b border-[#c0c0c0] {dollar}{o_brace}className{c_brace}`{c_brace}
      style={o_brace}{o_brace}
        backgroundColor: '{theme.background_color}',
        color: '{theme.text_color}',
      {c_brace}{c_brace}
    >
      <div className="max-w-4xl w-full flex flex-col items-center {classes_str}">
{content_html}
        <button 
          className="mt-4 px-6 py-2 rounded-lg font-semibold transition-colors duration-200"
          style={o_brace}{o_brace}
            backgroundColor: '{theme.primary_color}',
            color: '#ffffff'
          {c_brace}{c_brace}
          onClick={o_brace}() => alert('Click detected on {comp_name}'){c_brace}
        >
          Explore More
        </button>
      </div>
    </section>
  );
{c_brace}
"""
            components.append(
                GeneratedComponent(
                    name=comp_name,
                    code=code,
                    description=comp.description,
                )
            )

        global_styles = f"""/* Theme Variables */
:root {o_brace}
  --primary-color: {theme.primary_color};
  --secondary-color: {theme.secondary_color};
  --background-color: {theme.background_color};
  --text-color: {theme.text_color};
{c_brace}"""

        return CodegenResult(
            components=components,
            global_styles=global_styles,
        )
