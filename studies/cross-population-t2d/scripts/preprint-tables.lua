-- Allocate width to prose/identities, not sparse numeric columns. Preserve
-- semantic Pandoc table headers and alignment in both PDF and HTML output.
function Table(table)
  local widths = {
    [6] = {0.30, 0.13, 0.07, 0.08, 0.10, 0.32},
    [5] = {0.22, 0.08, 0.30, 0.22, 0.18},
    [4] = {0.38, 0.13, 0.28, 0.21}
  }
  local chosen = widths[#table.colspecs]
  if pandoc.utils.stringify(table.head):match("Specimen") then
    chosen = {0.27, 0.14, 0.22, 0.15, 0.22}
  end
  if chosen then
    for i, spec in ipairs(table.colspecs) do spec[2] = chosen[i] end
  end
  return table
end

-- Keep a table caption with its header/body, and each bibliographic entry
-- together. Editorial review found a stranded caption and split reference.
function Para(paragraph)
  local text = pandoc.utils.stringify(paragraph)
  if text:match("^%[%d+%]") then
    return {pandoc.RawBlock("latex", "\\begin{samepage}"), paragraph,
            pandoc.RawBlock("latex", "\\end{samepage}")}
  end
end

-- Use semantic table captions instead of detached paragraphs or manual breaks.
-- Longtable then keeps each caption with its own repeated header/body.
function Blocks(blocks)
  local out = pandoc.List()
  local i = 1
  while i <= #blocks do
    local block = blocks[i]
    local following = blocks[i + 1]
    local text = block.t == "Para" and pandoc.utils.stringify(block) or ""
    if following and following.t == "Table" and text:match("^Table %d+%.") then
      following.caption.long = {pandoc.Plain({pandoc.Str(text:gsub("^Table %d+%.%s*", ""))})}
      out:insert(following)
      i = i + 2
    else
      out:insert(block)
      i = i + 1
    end
  end
  return out
end
