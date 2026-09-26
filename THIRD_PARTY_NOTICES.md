# Third-party notices / 第三方说明

Original author notices are retained in the source files. The application's GPLv3 license applies to its original Python implementation; the MATLAB materials below keep their respective terms.

| Material | Source and terms |
| --- | --- |
| MOGOA and its original helper functions | Seyedali Mirjalili, [MOGOA distribution](https://www.mathworks.com/matlabcentral/fileexchange/63786-mogoa-multi-objective-grasshopper-optimization-algorithm). [BSD 2-Clause license](licenses/MOGOA-BSD-2-Clause.txt). Includes `MOGOA.m`, `dominates.m`, `HandleFullArchive.m`, `initialization.m`, `RankingProcess.m`, `RouletteWheelSelection.m`, `S_func.m` and `UpdateArchive.m`. |
| `UniformPoint.m`, `myHV.m`, `myIGD.m`, `myDM.m`, `myDeltaP.m` | BIMK Group, [PlatEMO](https://github.com/BIMK/PlatEMO), based on the project's version 4.7 materials. [Original research-use and citation notice](licenses/PlatEMO-notice.txt). These files are not relicensed as GPL. |
| `distance.m` | Roland Bunschoten, University of Amsterdam. Its retained notice permits modification and distribution with author acknowledgement. |
| Other MATLAB algorithms, adaptations and four Simulink models | Competition-team materials, included with confirmed publication permission. Existing authorship and terms are retained. The [recovery manifest](docs/provenance/recovered_dependencies.json) records recovered file sources. |
| `assets/school.jpg` and its embedded copy in `src/codes_rc.py` | Campus photograph included with confirmed publication permission. Image rights remain separate from the Python code license. |

When using PlatEMO-derived code in a publication, cite:

> Ye Tian, Ran Cheng, Xingyi Zhang, and Yaochu Jin. PlatEMO: A MATLAB Platform for Evolutionary Multi-Objective Optimization [Educational Forum]. IEEE Computational Intelligence Magazine, 12(4), 73–87, 2017.

MOGOA reference:

> S. Z. Mirjalili, S. Mirjalili, S. Saremi, H. Fatis, and H. Aljarah. Grasshopper optimization algorithm for multi-objective optimization problems. Applied Intelligence, 2017. DOI: 10.1007/s10489-017-1019-8.

## Installed dependencies

- **PyQt5:** GPLv3 or a commercial license from [Riverbank](https://www.riverbankcomputing.com/software/pyqt). The original Python application is published under GPLv3.
- **MATLAB, Simulink and toolboxes:** installed and licensed separately through MathWorks.
- **MATLAB Engine 24.2.2:** retains MathWorks' license, including its restriction to use with MathWorks products and services; see the license included in the installed package.
- **Other Python packages:** retain their individual licenses. Version pins and download hashes are in `requirements*.lock`.

## 中文

原创 Python 应用采用 GPLv3；MOGOA 保留 BSD 条款，PlatEMO 辅助函数保留研究使用及论文引用说明。团队算法、模型和校园照片已确认可公开，原有权属与条款继续有效。MATLAB 与 Python 依赖由使用者另行安装。
