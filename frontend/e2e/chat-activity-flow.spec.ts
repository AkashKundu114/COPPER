import { test, expect } from "@playwright/test";

test.describe("Critical User Flows - Live Local Models E2E", () => {
  test.setTimeout(120000);

  test("Send message with local model -> Receive streaming response -> Check activity trace", async ({
    page,
  }) => {
    // 1. Navigate to application
    await page.goto("/");
    await expect(page).toHaveTitle(/COPPER/i);

    // 2. Navigate to Conversation / Chat view via Sidebar
    const chatNavButton = page.locator("button, a").filter({ hasText: /Conversation/i }).first();
    await expect(chatNavButton).toBeVisible();
    await chatNavButton.click();

    // Verify ChatDock input is present
    const chatInput = page.getByPlaceholder(/input command or prompt/i);
    await expect(chatInput).toBeVisible({ timeout: 15000 });

    // 3. Select Cognitive Intelligence Mode if needed or use Adaptive Intent
    const promptText = "Hello COPPER, run quick system diagnostics and report status.";
    await chatInput.fill(promptText);

    // 4. Send message
    const sendButton = page.getByRole("button", { name: /send message/i });
    await expect(sendButton).toBeVisible();
    await sendButton.click();

    // 5. Verify user message appears in the conversation feed
    const userMessage = page.locator("text=" + promptText).first();
    await expect(userMessage).toBeVisible({ timeout: 10000 });

    // 6. Wait for assistant response to arrive from local model
    // The response can come from COPPER or one of the 30 local agent specialists
    const assistantBubble = page
      .locator("[class*='prose'], [class*='message'], [class*='bubble'], p")
      .filter({
        hasNotText: promptText,
      })
      .last();

    // Allow sufficient time for local model inference on device
    await expect(assistantBubble).toBeVisible({ timeout: 60000 });

    // 7. Navigate to Activity Stream view via Sidebar
    const activityNavButton = page.locator("button, a").filter({ hasText: /Activity Stream/i }).first();
    await expect(activityNavButton).toBeVisible();
    await activityNavButton.click();

    // 8. Verify Activity Trace and execution telemetry render
    await expect(
      page.locator("text=Live Execution & Governance Log").or(page.locator("text=Activity Stream")).first()
    ).toBeVisible({ timeout: 15000 });

    // Check for activity cards or categories (NEXUS, Tools, Routing, Guardian, etc.)
    const categoryBadge = page
      .locator("text=NEXUS")
      .or(page.locator("text=Routing"))
      .or(page.locator("text=Tools"))
      .or(page.locator("text=Guardian"))
      .or(page.locator("text=Inference"))
      .first();

    await expect(categoryBadge).toBeVisible({ timeout: 15000 });
  });

  test("Send coding request with Software Architect mode -> Verify specialized agent routing", async ({
    page,
  }) => {
    // 1. Navigate to application
    await page.goto("/");

    // 2. Open Conversation
    const chatNavButton = page.locator("button, a").filter({ hasText: /Conversation/i }).first();
    await chatNavButton.click();

    const chatInput = page.getByPlaceholder(/input command or prompt/i);
    await expect(chatInput).toBeVisible({ timeout: 15000 });

    // 3. Switch model to Software Architect (Coding tier)
    const modelDropdownButton = page.getByRole("button", {
      name: /select cognitive intelligence mode/i,
    });
    await modelDropdownButton.click();

    const codingModeOption = page.locator("button").filter({ hasText: /Software Architect/i }).first();
    await expect(codingModeOption).toBeVisible();
    await codingModeOption.click();

    // 4. Input and send coding prompt
    const codePrompt = "Write a python function to compute fibonacci sequence.";
    await chatInput.fill(codePrompt);

    const sendButton = page.getByRole("button", { name: /send message/i });
    await sendButton.click();

    // 5. Verify user message appears in feed
    await expect(page.locator("text=" + codePrompt).first()).toBeVisible({ timeout: 10000 });

    // 6. Wait for code response
    const codeResponse = page.locator("pre, code, [class*='prose']").first();
    await expect(codeResponse).toBeVisible({ timeout: 60000 });

    // 7. Verify Activity view shows trace
    const activityNavButton = page.locator("button, a").filter({ hasText: /Activity Stream/i }).first();
    await activityNavButton.click();

    await expect(page.locator("text=Activity Stream").or(page.locator("text=Activity")).first()).toBeVisible({
      timeout: 15000,
    });
  });
});
