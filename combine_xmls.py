import glob
import xml.etree.ElementTree as ET

if __name__ == "__main__":
    COMBINE = True

    if COMBINE:
        for report_date in [1871, 1872]:
            pages = glob.glob(f"data/raw/{report_date} Exported Files/XML/*/page/00*.xml")
            ordered_pages = sorted(pages, key=lambda x: int(x.split("\\")[-1].split("_")[0]))

            trees, roots = [], []
            for p in ordered_pages:
                if 'Table' not in p:
                    tree = ET.parse(p)
                    root = tree.getroot()

                trees.append(tree)
                roots.append(root)


            combined_root = roots[0]
            combined_tree = trees[0] 

            for root in roots[1:]:
                for child in root:
                    combined_root.append(child)

            ET.indent(combined_tree, space="    ")
            combined_tree.write(f"data/interim/{report_date}_combined_pages.xml", encoding="UTF-8")

