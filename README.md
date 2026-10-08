# CaloriesCounter-App

**Prato à Lupa**: PWA que estima calorias e macros de um prato a partir de um vídeo curto.
App: https://filipegomes-code.github.io/CaloriesCounter-App/

- A IA (Gemini ou Claude, com a chave de cada utilizador) identifica os alimentos e estima as gramas.
- As calorias e os macros por 100 g vêm de uma tabela de composição de alimentos (escolhida nas definições).
- Dias, refeições e definições ficam só no `localStorage` do aparelho. Use Exportar/Importar para cópias de segurança.

## Tabelas nutricionais

`data/insa.json` e `data/usda.json` são gerados por `tools/build_tables.py` (ver instruções no ficheiro).

- Fonte: Base de Dados da Composição de Alimentos. Instituto Nacional de Saúde Doutor Ricardo Jorge, I. P. - INSA. v 7.1 - 2026. https://portfir.insa.min-saude.pt/
- USDA FoodData Central, SR Legacy (2018-04), domínio público (CC0). https://fdc.nal.usda.gov/

Hidratos de carbono = hidratos disponíveis (sem fibra); nos dados USDA a fibra foi subtraída ao valor "by difference".
