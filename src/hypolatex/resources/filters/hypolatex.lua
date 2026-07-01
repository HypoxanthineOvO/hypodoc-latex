-- Pandoc Lua filter for HypoDoc Markdown directives.

local supported = {
  note = true,
  tip = true,
  warning = true,
  summary = true,
  question = true,
  hint = true,
  answer = true,
  solution = true,
  qa = true,
  objective = true,
  info = true,
  task = true,
  requirement = true,
  deliverable = true,
  checklist = true,
  rubric = true,
  figure = true,
  ref = true,
  table = true,
}

local environments = {
  note = "HypoNote",
  tip = "HypoTip",
  warning = "HypoWarning",
  summary = "HypoSummary",
  question = "HypoQuestion",
  hint = "HypoHint",
  answer = "HypoAnswer",
  solution = "HypoSolution",
  qa = "HypoQA",
  objective = "HypoObjective",
  info = "HypoInfo",
  task = "HypoTask",
  requirement = "HypoRequirement",
  deliverable = "HypoDeliverable",
  checklist = "HypoChecklist",
  rubric = "HypoRubric",
}

local supported_list = "note, tip, warning, summary, question, hint, answer, solution, qa, objective, info, task, requirement, deliverable, checklist, rubric, figure, ref, table"

local function first_class(div)
  if div.classes and #div.classes > 0 then
    return div.classes[1]
  end
  return nil
end

local function has_class(block, name)
  if block.classes == nil then
    return false
  end
  for _, class in ipairs(block.classes) do
    if class == name then
      return true
    end
  end
  return false
end

local function has_attribute_class(element, name)
  if element == nil or element.classes == nil then
    return false
  end
  for _, class in ipairs(element.classes) do
    if class == name then
      return true
    end
  end
  return false
end

local function directive_for_div(div)
  if has_class(div, "table") then
    return "table"
  end
  return first_class(div)
end

local function unsupported_directive(name)
  error(
    "unsupported directive '" .. name .. "'. Supported directives: " .. supported_list
  )
end

local function attr(div, name)
  return div.attributes[name] or ""
end

local function latex_escape(value)
  value = tostring(value or "")
  value = value:gsub("\\", "\\textbackslash{}")
  value = value:gsub("([%%$#&_{}])", "\\%1")
  value = value:gsub("~", "\\textasciitilde{}")
  value = value:gsub("%^", "\\textasciicircum{}")
  return value
end

local function raw_block(text)
  return pandoc.RawBlock("latex", text)
end

local function raw_code_block_environment(block)
  local text = tostring(block.text or "")
  if text:find("\\end{HypoCode", 1, true) then
    error("code block contains reserved HypoCode environment terminator")
  end

  text = text:gsub("\r\n", "\n"):gsub("\r", "\n")

  local nonempty_lines = 0
  for line in (text .. "\n"):gmatch("([^\n]*)\n") do
    if line:match("%S") then
      nonempty_lines = nonempty_lines + 1
    end
  end

  local environment = "HypoCodeBlock"
  if nonempty_lines <= 1 then
    environment = "HypoCodeCommand"
  end

  return raw_block(
    "\\begin{" .. environment .. "}\n" .. text .. "\n\\end{" .. environment .. "}"
  )
end

local function trim(value)
  value = tostring(value or "")
  return value:gsub("^%s+", ""):gsub("%s+$", "")
end

local function lower_trim(value)
  return trim(value):lower()
end

local function ends_with(value, suffix)
  return suffix ~= "" and value:sub(-#suffix) == suffix
end

local function normalize_figure_width(value)
  value = trim(value)
  if value == "" then
    return "0.86\\linewidth"
  end

  if value:match("^%d*%.?%d+$") then
    return value .. "\\linewidth"
  end

  local command_suffixes = {
    "\\linewidth",
    "\\textwidth",
    "\\columnwidth",
  }
  for _, suffix in ipairs(command_suffixes) do
    if ends_with(value, suffix) then
      local number = value:sub(1, #value - #suffix)
      if number:match("^%d*%.?%d+$") then
        return number .. suffix
      end
    end
  end

  local unit_suffixes = {
    "cm",
    "mm",
    "in",
    "pt",
    "bp",
    "em",
    "ex",
  }
  for _, suffix in ipairs(unit_suffixes) do
    if ends_with(value, suffix) then
      local number = trim(value:sub(1, #value - #suffix))
      if number:match("^%d*%.?%d+$") then
        return number .. suffix
      end
    end
  end

  error(
    "invalid figure width '"
      .. value
      .. "'. Use a number such as width=\"0.92\" or a safe TeX dimension."
  )
end

local function normalize_figure_placement(value)
  value = trim(value)
  if value == "" then
    return "htbp"
  end

  local aliases = {
    fixed = "H",
    here = "H",
    float = "htbp",
  }
  if aliases[value] ~= nil then
    return aliases[value]
  end

  local allowed = {
    H = true,
    h = true,
    t = true,
    b = true,
    p = true,
    ht = true,
    hb = true,
    hp = true,
    tb = true,
    tp = true,
    bp = true,
    htbp = true,
    htp = true,
    tbp = true,
    ["!h"] = true,
    ["!ht"] = true,
    ["!htbp"] = true,
  }

  if allowed[value] then
    return value
  end

  error(
    "invalid figure placement '"
      .. value
      .. "'. Use placement=\"H\" for fixed figures or omit it for htbp."
  )
end

local function content_latex(content)
  local doc = pandoc.Pandoc(content)
  local latex = pandoc.write(doc, "latex", { wrap_text = "none" })
  latex = latex:gsub("^%s+", ""):gsub("%s+$", "")
  latex = latex:gsub("\n  ([^%s])", "\n%1")
  latex = latex:gsub("\\def\\labelenumi{\\arabic{enumi}%.}\n", "")
  return latex
end

local function cell_latex(content)
  local latex = content_latex(content)
  latex = latex:gsub("\n%s*\n", "\\par ")
  latex = latex:gsub("%s*\n%s*", " ")
  return latex
end

local function meta_scalar(value)
  if value == nil then
    return nil
  end

  local value_type = pandoc.utils.type(value)
  if value_type == "boolean" then
    return value and "true" or "false"
  end
  if value_type == "string" then
    return value
  end
  if value_type == "Inlines" or value_type == "Blocks" then
    return pandoc.utils.stringify(value)
  end

  return pandoc.utils.stringify(value)
end

local function yaml_code_block(block)
  return block ~= nil and block.t == "CodeBlock" and has_class(block, "yaml")
end

local function yaml_table_config_candidate(block)
  if not yaml_code_block(block) then
    return false
  end

  local text = tostring(block.text or "")
  local keys = {
    "type",
    "density",
    "width",
    "caption",
    "label",
    "header",
    "striped",
    "long",
    "columns",
  }
  for _, key in ipairs(keys) do
    if text:match("^%s*" .. key .. "%s*:") or text:match("\n%s*" .. key .. "%s*:") then
      return true
    end
  end
  return false
end

local function parse_table_yaml(text)
  local ok, parsed = pcall(
    pandoc.read,
    "---\n" .. tostring(text or "") .. "\n---\n",
    "markdown+yaml_metadata_block"
  )
  if not ok then
    error("invalid .table yaml config: " .. tostring(parsed))
  end
  return parsed.meta or {}
end

local function parse_bool(value, default)
  if value == nil or trim(value) == "" then
    return default
  end

  local normalized = lower_trim(value)
  local truthy = {
    ["true"] = true,
    ["yes"] = true,
    ["y"] = true,
    ["1"] = true,
    ["on"] = true,
  }
  local falsy = {
    ["false"] = true,
    ["no"] = true,
    ["n"] = true,
    ["0"] = true,
    ["off"] = true,
  }

  if truthy[normalized] then
    return true
  end
  if falsy[normalized] then
    return false
  end

  error("invalid .table boolean value '" .. tostring(value) .. "'")
end

local function bool_string(value)
  return value and "true" or "false"
end

local function normalize_label(value)
  value = trim(value)
  if value == "" then
    return ""
  end
  if not value:match("^[%w%-%._:/]+$") then
    error(
      "invalid table label '"
        .. value
        .. "'. Use letters, numbers, '-', '_', '.', ':', or '/'."
    )
  end
  return value
end

local function normalize_pattern(value)
  value = lower_trim(value)
  if value == "" then
    return "default"
  end

  local aliases = {
    ["cheatsheet/compact"] = "cheatsheet",
    compact_table = "compact",
  }
  value = aliases[value] or value

  local allowed = {
    default = true,
    comparison = true,
    checklist = true,
    rubric = true,
    cheatsheet = true,
    compact = true,
    long = true,
  }
  if allowed[value] then
    return value
  end

  error(
    "invalid table type '"
      .. value
      .. "'. Supported table types: comparison, checklist, rubric, cheatsheet, compact, long."
  )
end

local function normalize_density(value, pattern)
  value = lower_trim(value)
  if value == "" then
    if
      pattern == "comparison"
      or pattern == "checklist"
      or pattern == "cheatsheet"
      or pattern == "compact"
    then
      return "compact"
    end
    return "normal"
  end

  local aliases = {
    dense = "compact",
    relaxed = "comfortable",
  }
  value = aliases[value] or value

  local allowed = {
    compact = true,
    normal = true,
    comfortable = true,
  }
  if allowed[value] then
    return value
  end

  error(
    "invalid table density '"
      .. value
      .. "'. Supported densities: compact, normal, comfortable."
  )
end

local function normalize_table_width(value)
  value = trim(value)
  if value == "" then
    return "\\linewidth"
  end

  if value:match("^%d*%.?%d+$") then
    return value .. "\\linewidth"
  end

  local command_suffixes = {
    "\\linewidth",
    "\\textwidth",
    "\\columnwidth",
  }
  for _, suffix in ipairs(command_suffixes) do
    if value == suffix then
      return value
    end
    if ends_with(value, suffix) then
      local number = trim(value:sub(1, #value - #suffix))
      if number:match("^%d*%.?%d+$") then
        return number .. suffix
      end
    end
  end

  error(
    "invalid table width '"
      .. value
      .. "'. Use a number such as width=\"0.92\" or a safe TeX line width."
  )
end

local function normalize_column_width(value, fallback)
  value = trim(value)
  if value == "" then
    return fallback
  end

  local percent = value:match("^(%d*%.?%d+)%%$")
  if percent ~= nil then
    return tostring(tonumber(percent) / 100) .. "\\linewidth"
  end

  if value:match("^%d*%.?%d+$") then
    return value .. "\\linewidth"
  end

  if value == "\\linewidth" then
    return "1\\linewidth"
  end
  if ends_with(value, "\\linewidth") then
    local number = trim(value:sub(1, #value - #"\\linewidth"))
    if number:match("^%d*%.?%d+$") then
      return number .. "\\linewidth"
    end
  end

  error(
    "invalid table column width '"
      .. value
      .. "'. Use a number such as width: 0.25 or a safe \\linewidth fraction."
  )
end

local function normalize_weight(value)
  value = trim(value)
  if value == "" then
    return "1"
  end
  if value:match("^%d*%.?%d+$") then
    return value
  end
  error("invalid table column weight '" .. value .. "'. Use a positive number.")
end

local function normalize_align(value, fallback)
  value = lower_trim(value)
  if value == "" then
    value = fallback or "left"
  end

  local aliases = {
    l = "left",
    left = "left",
    default = "left",
    c = "center",
    center = "center",
    centre = "center",
    r = "right",
    right = "right",
  }
  local normalized = aliases[value]
  if normalized ~= nil then
    return normalized
  end

  error(
    "invalid table column alignment '"
      .. value
      .. "'. Supported alignments: left, center, right."
  )
end

local function pandoc_align(value)
  local align = tostring(value or "")
  local aliases = {
    AlignLeft = "left",
    AlignCenter = "center",
    AlignRight = "right",
    AlignDefault = "left",
  }
  return aliases[align] or "left"
end

local function format_fraction(value)
  local formatted = string.format("%.4f", value)
  formatted = formatted:gsub("0+$", ""):gsub("%.$", ".0")
  return formatted
end

local function table_rowsep(density)
  if density == "compact" then
    return "1.6pt"
  end
  if density == "comfortable" then
    return "5pt"
  end
  return "3pt"
end

local function long_arraystretch(density)
  if density == "compact" then
    return "0.94"
  end
  if density == "comfortable" then
    return "1.16"
  end
  return "1.04"
end

local function read_yaml_table_config(meta)
  local config = {}
  local keys = {
    "type",
    "long",
    "density",
    "width",
    "caption",
    "label",
    "header",
    "striped",
  }
  for _, key in ipairs(keys) do
    if meta[key] ~= nil then
      config[key] = meta_scalar(meta[key])
    end
  end

  config.columns = {}
  local columns = meta.columns
  if columns ~= nil then
    for index = 1, #columns do
      local source = columns[index]
      local column = {}
      if source.align ~= nil then
        column.align = meta_scalar(source.align)
      end
      if source.width ~= nil then
        column.width = meta_scalar(source.width)
      end
      if source.weight ~= nil then
        column.weight = meta_scalar(source.weight)
      end
      config.columns[index] = column
    end
  end
  return config
end

local function table_config(div, yaml_config)
  local config = {
    type = attr(div, "type"),
    long = attr(div, "long"),
    density = attr(div, "density"),
    width = attr(div, "width"),
    caption = attr(div, "caption"),
    label = attr(div, "label"),
    header = attr(div, "header"),
    striped = attr(div, "striped"),
    columns = {},
  }

  if yaml_config ~= nil then
    for key, value in pairs(yaml_config) do
      if key ~= "columns" then
        config[key] = value
      end
    end
    if yaml_config.columns ~= nil then
      config.columns = yaml_config.columns
    end
  end

  config.type = normalize_pattern(config.type)
  config.long = parse_bool(config.long, config.type == "long")
  if config.type == "long" then
    config.long = true
  end
  config.density = normalize_density(config.density, config.type)
  config.width = normalize_table_width(config.width)
  config.caption = latex_escape(config.caption)
  config.label = normalize_label(config.label)
  config.header = parse_bool(config.header, true)
  config.striped = parse_bool(
    config.striped,
    config.type == "comparison"
      or config.type == "rubric"
      or config.type == "cheatsheet"
      or config.type == "compact"
  )

  return config
end

local function consume_table_yaml(content)
  local rest = {}
  local yaml_config = nil
  local start = 1

  if yaml_code_block(content[1]) then
    yaml_config = read_yaml_table_config(parse_table_yaml(content[1].text))
    start = 2
  end

  for index = start, #content do
    rest[#rest + 1] = content[index]
  end

  return rest, yaml_config
end

local function controlled_table_from_content(content)
  local found = nil
  for _, block in ipairs(content) do
    if block.t == "Table" then
      if found ~= nil then
        error(".table directive supports exactly one Markdown table")
      end
      found = block
    elseif block.t == "Para" and pandoc.utils.stringify(block):match("^%s*$") then
      -- Ignore empty paragraphs produced by forgiving Markdown input.
    else
      error(".table directive content must be one Markdown table after optional yaml config")
    end
  end

  if found == nil then
    error(".table directive requires a Markdown table")
  end
  return found
end

local function table_column_count(table_block)
  local count = #table_block.colspecs
  for _, row in ipairs(table_block.head.rows or {}) do
    count = math.max(count, #row.cells)
  end
  for _, body in ipairs(table_block.bodies or {}) do
    for _, row in ipairs(body.head or {}) do
      count = math.max(count, #row.cells)
    end
    for _, row in ipairs(body.body or {}) do
      count = math.max(count, #row.cells)
    end
  end
  return count
end

local function table_columns(table_block, config)
  local count = table_column_count(table_block)
  if count < 1 then
    error(".table directive requires at least one table column")
  end

  local columns = {}
  local fallback_width = format_fraction(0.95 / count) .. "\\linewidth"
  for index = 1, count do
    local source = config.columns[index] or {}
    local colspec = table_block.colspecs[index]
    local fallback_align = "left"
    if colspec ~= nil then
      fallback_align = pandoc_align(colspec[1])
    end
    columns[index] = {
      align = normalize_align(source.align, fallback_align),
      width = normalize_column_width(source.width, fallback_width),
      weight = normalize_weight(source.weight),
      explicit_width = trim(source.width or "") ~= "",
    }
  end
  return columns
end

local function tblr_align(value)
  local aliases = {
    left = "l",
    center = "c",
    right = "r",
  }
  return aliases[value] or "l"
end

local function long_align_prefix(value)
  if value == "center" then
    return ">{\\centering\\arraybackslash}"
  end
  if value == "right" then
    return ">{\\raggedleft\\arraybackslash}"
  end
  return ">{\\raggedright\\arraybackslash}"
end

local function tblr_colspec(columns)
  local specs = {}
  for _, column in ipairs(columns) do
    local align = tblr_align(column.align)
    if column.explicit_width then
      specs[#specs + 1] = "Q[" .. align .. ",wd=" .. column.width .. "]"
    else
      specs[#specs + 1] = "X[" .. column.weight .. "," .. align .. "]"
    end
  end
  return table.concat(specs, "")
end

local function long_colspec(columns)
  local specs = {}
  for _, column in ipairs(columns) do
    specs[#specs + 1] = long_align_prefix(column.align) .. "p{" .. column.width .. "}"
  end
  return "@{}" .. table.concat(specs, "") .. "@{}"
end

local function column_macros(columns)
  local lines = {}
  for _, column in ipairs(columns) do
    lines[#lines + 1] =
      "\\HypoTableColumn{align="
      .. column.align
      .. ",width="
      .. column.width
      .. ",weight="
      .. column.weight
      .. "}"
  end
  return lines
end

local function table_config_macro(config)
  return "\\HypoTableConfig{type="
    .. config.type
    .. ",density="
    .. config.density
    .. ",width="
    .. config.width
    .. ",caption={"
    .. config.caption
    .. "},label={"
    .. config.label
    .. "},header="
    .. bool_string(config.header)
    .. ",striped="
    .. bool_string(config.striped)
    .. "}"
end

local function add_float_caption(lines, config)
  if config.caption == "" and config.label == "" then
    return
  end

  if config.caption == "" then
    lines[#lines + 1] = "\\caption{}"
  else
    lines[#lines + 1] = "\\caption{" .. config.caption .. "}"
  end
  if config.label ~= "" then
    lines[#lines + 1] = "\\label{" .. config.label .. "}"
  end
end

local function render_row(row, column_count)
  local rendered = {}
  for index = 1, column_count do
    local cell = row.cells[index]
    if cell == nil then
      rendered[#rendered + 1] = ""
    else
      if cell.row_span ~= 1 or cell.col_span ~= 1 then
        error(".table directive does not support row spans or column spans")
      end
      rendered[#rendered + 1] = cell_latex(cell.contents)
    end
  end
  return table.concat(rendered, " & ") .. " \\\\"
end

local function collect_rows(table_block)
  local head_rows = {}
  for _, row in ipairs(table_block.head.rows or {}) do
    head_rows[#head_rows + 1] = row
  end

  local body_rows = {}
  for _, body in ipairs(table_block.bodies or {}) do
    for _, row in ipairs(body.head or {}) do
      body_rows[#body_rows + 1] = row
    end
    for _, row in ipairs(body.body or {}) do
      body_rows[#body_rows + 1] = row
    end
  end
  for _, row in ipairs(table_block.foot.rows or {}) do
    body_rows[#body_rows + 1] = row
  end

  return head_rows, body_rows
end

local function rendered_rows(rows, column_count)
  local rendered = {}
  for _, row in ipairs(rows) do
    rendered[#rendered + 1] = render_row(row, column_count)
  end
  return rendered
end

local function render_tblr_table(config, columns, head_rows, body_rows)
  local column_count = #columns
  local lines = { table_config_macro(config) }
  for _, line in ipairs(column_macros(columns)) do
    lines[#lines + 1] = line
  end

  local options = {
    "width=" .. config.width,
    "colspec={" .. tblr_colspec(columns) .. "}",
    "rowsep=" .. table_rowsep(config.density),
    "hline{1,Z}={0.08em}",
  }
  if config.header and #head_rows > 0 then
    options[#options + 1] = "row{1}={font=\\bfseries}"
    options[#options + 1] = "hline{2}={0.04em}"
  end
  if config.striped then
    options[#options + 1] = "row{even}={bg=HypoTableStripe}"
  end

  lines[#lines + 1] = "\\begin{table}[htbp]"
  lines[#lines + 1] = "\\centering"
  add_float_caption(lines, config)
  lines[#lines + 1] = "\\begin{tblr}{"
  lines[#lines + 1] = table.concat(options, ",")
  lines[#lines + 1] = "}"
  if config.header and #head_rows > 0 then
    for _, row in ipairs(rendered_rows(head_rows, column_count)) do
      lines[#lines + 1] = row
    end
  else
    for _, row in ipairs(rendered_rows(head_rows, column_count)) do
      lines[#lines + 1] = row
    end
  end
  for _, row in ipairs(rendered_rows(body_rows, column_count)) do
    lines[#lines + 1] = row
  end
  lines[#lines + 1] = "\\end{tblr}"
  lines[#lines + 1] = "\\end{table}"
  return raw_block(table.concat(lines, "\n"))
end

local function add_long_caption(lines, config)
  if config.caption == "" and config.label == "" then
    return
  end

  local caption = config.caption
  if caption == "" then
    caption = " "
  end
  local line = "\\caption{" .. caption .. "}"
  if config.label ~= "" then
    line = line .. "\\label{" .. config.label .. "}"
  end
  lines[#lines + 1] = line .. " \\\\"
end

local function render_long_table(config, columns, head_rows, body_rows)
  local column_count = #columns
  local header = rendered_rows(head_rows, column_count)
  local body = rendered_rows(body_rows, column_count)
  local lines = { table_config_macro(config) }
  for _, line in ipairs(column_macros(columns)) do
    lines[#lines + 1] = line
  end

  lines[#lines + 1] = "\\begingroup"
  lines[#lines + 1] = "\\renewcommand{\\arraystretch}{" .. long_arraystretch(config.density) .. "}"
  if config.striped then
    lines[#lines + 1] = "\\rowcolors{2}{HypoTableStripe}{white}"
  end
  lines[#lines + 1] = "\\begin{longtable}{" .. long_colspec(columns) .. "}"
  add_long_caption(lines, config)

  lines[#lines + 1] = "\\toprule"
  if config.header and #header > 0 then
    for _, row in ipairs(header) do
      lines[#lines + 1] = row
    end
    lines[#lines + 1] = "\\midrule"
    lines[#lines + 1] = "\\endfirsthead"
    lines[#lines + 1] = "\\toprule"
    for _, row in ipairs(header) do
      lines[#lines + 1] = row
    end
    lines[#lines + 1] = "\\midrule"
    lines[#lines + 1] = "\\endhead"
  else
    lines[#lines + 1] = "\\endfirsthead"
    lines[#lines + 1] = "\\endhead"
    for _, row in ipairs(header) do
      body[#body + 1] = row
    end
  end
  lines[#lines + 1] = "\\bottomrule"
  lines[#lines + 1] = "\\endfoot"

  for _, row in ipairs(body) do
    lines[#lines + 1] = row
  end
  lines[#lines + 1] = "\\bottomrule"
  lines[#lines + 1] = "\\end{longtable}"
  if config.striped then
    lines[#lines + 1] = "\\rowcolors{2}{}{}"
  end
  lines[#lines + 1] = "\\endgroup"
  return raw_block(table.concat(lines, "\n"))
end

local function render_controlled_table(div)
  local content, yaml_config = consume_table_yaml(div.content)
  local table_block = controlled_table_from_content(content)
  local config = table_config(div, yaml_config)
  local columns = table_columns(table_block, config)
  local head_rows, body_rows = collect_rows(table_block)

  if config.long then
    return render_long_table(config, columns, head_rows, body_rows)
  end
  return render_tblr_table(config, columns, head_rows, body_rows)
end

local function normalize_answer_hyphens(value)
  value = value:gsub("\226\128\144", "-")
  value = value:gsub("\226\128\145", "-")
  value = value:gsub("\226\128\146", "-")
  value = value:gsub("\226\136\146", "-")
  return value
end

local function normalize_question_style(value)
  value = lower_trim(value)
  if value == "" then
    return ""
  end

  local aliases = {
    default = "outline",
    restrained = "outline",
    text = "plain",
    inline = "plain",
    review = "card",
  }
  value = aliases[value] or value

  local allowed = {
    plain = true,
    outline = true,
    card = true,
  }
  if allowed[value] then
    return value
  end

  error(
    "invalid question style '"
      .. value
      .. "'. Supported question styles: plain, outline, card."
  )
end

local function optional_args_text(values)
  if values == nil then
    return ""
  end

  local last_nonempty = 0
  for index, value in ipairs(values) do
    if value ~= nil and value ~= "" then
      last_nonempty = index
    end
  end

  local text = ""
  for index, value in ipairs(values) do
    if index > last_nonempty then
      break
    end
    if value ~= nil and value ~= "" then
      text = text .. "[" .. value .. "]"
    else
      text = text .. "[]"
    end
  end
  return text
end

local function manual_heading_prefix(value)
  value = tostring(value or "")
  if value:match("^%d+[%.)、．]$") then
    return true
  end
  if value:match("^%d+%.%d+[%.%d]*[%.、．]?$") then
    return true
  end
  if value:match("^%(%d+%)$") then
    return true
  end
  if value:match("^%d+%)$") then
    return true
  end
  if value:match("^[A-Za-z][%.)]$") then
    return true
  end
  if value:match("^[一二三四五六七八九十百千]+[、．.]$") then
    return true
  end
  if value:match("^第[一二三四五六七八九十百千]+[章节篇部]$") then
    return true
  end
  if value:match("^%([一二三四五六七八九十百千]+%)$") then
    return true
  end
  return false
end

local function heading_starts_with_manual_number(header)
  local content = header.content or {}
  for _, inline in ipairs(content) do
    if inline.t == "Space" or inline.t == "SoftBreak" or inline.t == "LineBreak" then
      -- skip leading whitespace
    elseif inline.t == "Str" then
      return manual_heading_prefix(inline.text)
    else
      return false
    end
  end
  return false
end

local function environment_blocks(name, content, optional_args)
  local latex = content_latex(content)
  if name == "HypoAnswer" then
    latex = normalize_answer_hyphens(latex)
  end

  local begin_environment = "\\begin{" .. name .. "}"
  begin_environment = begin_environment .. optional_args_text(optional_args)

  return raw_block(
    begin_environment .. "\n" .. latex .. "\n\\end{" .. name .. "}"
  )
end

function Header(header)
  local manual_number = has_attribute_class(header, "manual-number")
  local unnumbered = has_attribute_class(header, "unnumbered")
  local suspicious_manual_number = heading_starts_with_manual_number(header)

  if suspicious_manual_number and not manual_number and not unnumbered then
    error(
      "heading appears to contain a manual number but is not marked: '"
        .. pandoc.utils.stringify(header.content)
        .. "'. Remove the manual number for automatic numbering, or add "
        .. "{.manual-number} to keep it, or {.unnumbered} for an unnumbered heading."
    )
  end

  if manual_number or unnumbered then
    table.insert(header.classes, "unnumbered")
  end

  header.identifier = ""
  return header
end

function CodeBlock(block)
  if yaml_table_config_candidate(block) then
    return block
  end
  return raw_code_block_environment(block)
end

function Div(div)
  local directive = directive_for_div(div)
  if directive == nil then
    return div
  end

  if not supported[directive] then
    unsupported_directive(directive)
  end

  local environment = environments[directive]
  if environment ~= nil then
    if directive == "question" then
      local label = latex_escape(attr(div, "label"))
      local title = latex_escape(attr(div, "title"))
      local numbered = lower_trim(attr(div, "numbered"))
      local style = normalize_question_style(attr(div, "style"))
      if style == "" and numbered == "" then
        return environment_blocks(environment, div.content, { label, title })
      end
      return environment_blocks(environment, div.content, { label, title, numbered, style })
    end
    if directive == "qa" then
      return environment_blocks(environment, div.content, {
        latex_escape(attr(div, "title")),
        normalize_question_style(attr(div, "style")),
      })
    end
    if directive == "hint" or directive == "answer" or directive == "solution" then
      return environment_blocks(environment, div.content, {
        latex_escape(attr(div, "title")),
        normalize_question_style(attr(div, "style")),
      })
    end
    return environment_blocks(environment, div.content, { latex_escape(attr(div, "title")) })
  end

  if directive == "table" then
    return render_controlled_table(div)
  end

  if directive == "figure" then
    return raw_block(
      "\\HypoFigureEx{"
        .. latex_escape(attr(div, "label"))
        .. "}{"
        .. latex_escape(attr(div, "src"))
        .. "}{"
        .. latex_escape(attr(div, "caption"))
        .. "}{"
        .. normalize_figure_width(attr(div, "width"))
        .. "}{"
        .. normalize_figure_placement(attr(div, "placement"))
        .. "}"
    )
  end

  if directive == "ref" then
    return raw_block("\\HypoRef{" .. latex_escape(attr(div, "target")) .. "}")
  end

  return div
end
