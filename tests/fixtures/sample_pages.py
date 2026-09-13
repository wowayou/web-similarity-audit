"""Sample HTML pages for testing."""

SAMPLE_PAGE_1 = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Product A - Industrial Widgets</title>
</head>
<body>
    <header>
        <nav>
            <a href="/">Home</a>
            <a href="/products">Products</a>
            <a href="/about">About</a>
        </nav>
    </header>
    <main>
        <article>
            <h1>Industrial Widget Type A</h1>
            <p>Our Type A industrial widget is designed for heavy-duty applications in manufacturing environments. 
            With a load capacity of 5000kg and precision engineering, this widget delivers reliable performance 
            in the most demanding conditions.</p>
            <ul>
                <li>Load capacity: 5000kg</li>
                <li>Material: Hardened steel</li>
                <li>Warranty: 5 years</li>
                <li>Certification: ISO 9001</li>
            </ul>
            <h2>Technical Specifications</h2>
            <p>The Type A widget features advanced hydraulic systems and automated control mechanisms. 
            Installation is straightforward and can be completed in under two hours with standard tools.</p>
        </article>
    </main>
    <footer>
        <p>&copy; 2025 Industrial Widgets Inc. All rights reserved.</p>
    </footer>
</body>
</html>"""

SAMPLE_PAGE_2 = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Product B - Industrial Widgets</title>
</head>
<body>
    <header>
        <nav>
            <a href="/">Home</a>
            <a href="/products">Products</a>
            <a href="/about">About</a>
        </nav>
    </header>
    <main>
        <article>
            <h1>Industrial Widget Type B</h1>
            <p>Our Type B industrial widget is designed for heavy-duty applications in manufacturing environments. 
            With a load capacity of 7500kg and precision engineering, this widget delivers reliable performance 
            in the most demanding conditions.</p>
            <ul>
                <li>Load capacity: 7500kg</li>
                <li>Material: Hardened steel</li>
                <li>Warranty: 5 years</li>
                <li>Certification: ISO 9001</li>
            </ul>
            <h2>Technical Specifications</h2>
            <p>The Type B widget features advanced hydraulic systems and automated control mechanisms. 
            Installation is straightforward and can be completed in under two hours with standard tools.</p>
        </article>
    </main>
    <footer>
        <p>&copy; 2025 Industrial Widgets Inc. All rights reserved.</p>
    </footer>
</body>
</html>"""

SAMPLE_PAGE_3 = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Company History - Industrial Widgets</title>
</head>
<body>
    <header>
        <nav>
            <a href="/">Home</a>
            <a href="/products">Products</a>
            <a href="/about">About</a>
        </nav>
    </header>
    <main>
        <article>
            <h1>Our Company History</h1>
            <p>Founded in 1985, Industrial Widgets Inc. has been a pioneer in manufacturing solutions 
            for over three decades. Our commitment to quality and innovation has made us a trusted 
            partner for businesses worldwide.</p>
            <h2>Milestones</h2>
            <ul>
                <li>1985: Company founded in Detroit, Michigan</li>
                <li>1992: First international expansion to Europe</li>
                <li>2005: ISO 9001 certification achieved</li>
                <li>2018: Launch of automated widget production line</li>
            </ul>
            <p>Today, we serve over 500 customers across 30 countries, delivering excellence in every product.</p>
        </article>
    </main>
    <footer>
        <p>&copy; 2025 Industrial Widgets Inc. All rights reserved.</p>
    </footer>
</body>
</html>"""

SAMPLE_PAGE_CHINESE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>产品 A - 工业设备</title>
</head>
<body>
    <header>
        <nav>
            <a href="/">首页</a>
            <a href="/products">产品</a>
            <a href="/about">关于</a>
        </nav>
    </header>
    <main>
        <article>
            <h1>工业设备 A 型</h1>
            <p>我们的 A 型工业设备专为制造环境中的重型应用而设计。
            承载能力达 5000 公斤，精密工程设计，可在最苛刻的条件下提供可靠性能。</p>
            <ul>
                <li>承载能力：5000 公斤</li>
                <li>材料：硬化钢</li>
                <li>保修：5 年</li>
                <li>认证：ISO 9001</li>
            </ul>
            <h2>技术规格</h2>
            <p>A 型设备配备先进的液压系统和自动化控制机制。
            安装简单，使用标准工具可在两小时内完成。</p>
        </article>
    </main>
    <footer>
        <p>&copy; 2025 工业设备公司版权所有。</p>
    </footer>
</body>
</html>"""

SAMPLE_PAGE_NO_MAIN = """<!DOCTYPE html>
<html>
<head>
    <title>Page Without Main Content</title>
</head>
<body>
    <div id="wrapper">
        <div class="header">Navigation here</div>
        <div class="content">
            <p>This page lacks semantic HTML tags like main or article.</p>
        </div>
        <div class="footer">Footer here</div>
    </div>
</body>
</html>"""

SAMPLE_PAGE_EXACT_DUPLICATE = SAMPLE_PAGE_1  # Exact copy for SHA-256 testing

SAMPLE_PAGE_PARAPHRASED = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Widget Product A - Manufacturing Equipment</title>
</head>
<body>
    <header>
        <nav>
            <a href="/">Home</a>
            <a href="/products">Products</a>
            <a href="/about">About</a>
        </nav>
    </header>
    <main>
        <article>
            <h1>Type A Industrial Equipment</h1>
            <p>The Type A industrial equipment from our catalog is engineered for demanding manufacturing 
            applications. Featuring precision construction and a 5000kg weight capacity, it ensures 
            dependable operation under extreme conditions.</p>
            <ul>
                <li>Weight capacity: 5000kg</li>
                <li>Construction: Steel (hardened)</li>
                <li>Guarantee period: 5 years</li>
                <li>Quality standard: ISO 9001</li>
            </ul>
            <h2>Specifications</h2>
            <p>Advanced hydraulic technology and automated controls are built into the Type A model. 
            Setup is simple and typically takes less than two hours using common tools.</p>
        </article>
    </main>
    <footer>
        <p>&copy; 2025 Industrial Widgets Inc. All rights reserved.</p>
    </footer>
</body>
</html>"""
